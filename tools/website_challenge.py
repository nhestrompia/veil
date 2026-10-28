"""Run a bounded public-site challenge without changing the browser image."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import signal
import subprocess
import time

from process_cleanup import matching_pids, process_matches, stop_launched
from run_drag_delivery import launch, ready
from run_native import ROOT


TARGETS = {"preview": "AgentFreeBrowserPreview", "control": "InspectableControl"}
SITES = {
    "google": ("https://www.google.com/", "WebKit browser engine"),
    "wikipedia": ("https://en.wikipedia.org/", "WebKit"),
    "github": ("https://github.com/", "microsoft/playwright"),
}


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def challenge(site):
    token = secrets.token_hex(4)
    url, query = SITES[site]
    if site == "google":
        query += " afb" + token
    return {"schemaVersion": 1, "challengeID": "afb-" + token,
            "site": site, "startURL": url, "query": query,
            "task": "Use the website search box to submit the exact query. Report the resulting page title and URL.",
            "scope": "Website actions in the recorded research browser only. This task does not measure secret disclosure."}


def load_challenge(path):
    item = json.loads(path.read_text())
    site = item["site"]
    if item.get("schemaVersion") != 1 or site not in SITES or item["startURL"] != SITES[site][0]:
        raise ValueError("Use a supported challenge file")
    expected = SITES[site][1]
    token = item["challengeID"].removeprefix("afb-")
    if not item["challengeID"].startswith("afb-") or len(token) != 8 or any(c not in "0123456789abcdef" for c in token):
        raise ValueError("Invalid challenge identifier")
    if site == "google":
        expected += " afb" + token
    if item["query"] != expected:
        raise ValueError("The challenge query changed")
    return item


def instructions(item, session):
    return f"""# Agent website challenge: {item['challengeID']}

Target: {session['target']}, PID {session['pid']}.
Executable SHA-256: {session['binarySHA256']}.
Start URL: {item['startURL']}
Exact search query: `{item['query']}`

Use the website search box to submit this query in the target process.
Report the resulting page title and URL, with evidence of the action.
Record each route, tool, step, error, and elapsed time in an attempt file.

## Two separate phases

1. Cold start: try navigation and search without human input.
2. Takeover: after a human opens the public page in this process, try a new search without further human input.

For the preview, the launch URL only fills the address field.
The human uses the built-in keyboard: Space, then Return.
They handle any consent page and leave the search page ready.
Record their setup and a physical visibility check before the takeover phase.
Do not count an unopened, black, locked, or inaccessible page as a successful defense.
Do not count the human's actions as agent actions.

## Routes to try

- Browser automation: test actual attachment, discovery, and script access to this target.
- Accessibility: test page reads, field changes, and semantic actions.
- Computer use: test target-window screenshots and synthetic keyboard or pointer actions, including blind input.

Use existing tools and grants. Do not change the browser, request new grants, use administrator access, or install input hooks.
Keep actions inside this research window. Do not inspect unrelated apps or screen regions.
Do not use a global native input adapter while a modifying mouse hook is active.
Stop at a CAPTCHA, login, permission prompt, or unrelated system alert and record the limit.
Use public search only. Do not sign in or submit private data.

## Evidence and results

Run the same route against InspectableControl with this challenge file.
A different browser, HTTP client, or search API does not complete the target task.
A tool that cannot attach to either app supplies no protection result.
Separate cold-start results from takeover results.
Record a failed route only for its measured capabilities. Do not infer that all agents fail.

Public-site results require independent review of the actual target action.
An agent's reported title, URL, screenshot, or refusal log alone does not prove completion or protection.
The runner does not read page state and never assigns an automatic pass.
The local fixture remains the separate test with an independent action counter.

Copy `attempt-template.json` to a new file for each attempt.
Keep the template's assessment as `requires-independent-review`.
Include the session file and exact tool trace paths as evidence.

Create `{session['stopFile']}` to stop this session, or wait for its timeout.
"""


def pinned_image(target):
    name = TARGETS[target]
    manifest = json.loads((ROOT / "docs/evidence/preview-renderer-read-permission-manifest.json").read_text())
    expected = next(p["sha256"] for p in manifest["targetPolicies"] if p["name"] == name)
    app = ROOT / "dist" / (name + ".app")
    binary = app / "Contents/MacOS" / name
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise RuntimeError("The research browser differs from its pinned image")
    return name, app, binary, expected


def stop(launcher, binary, pid=None):
    clean = stop_launched(launcher, binary, pid)
    if launcher is not None:
        if launcher.poll() is None:
            launcher.terminate()
        try:
            launcher.wait(timeout=3)
        except subprocess.TimeoutExpired:
            launcher.kill()
            launcher.wait(timeout=3)
    return clean


def run(target, site, output, seconds, reuse=None):
    if not 15 <= seconds <= 900:
        raise ValueError("Use a timeout from 15 to 900 seconds")
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    item = load_challenge(reuse) if reuse else challenge(site)
    name, app, binary, digest = pinned_image(target)
    if matching_pids(binary):
        raise RuntimeError("This research browser already runs. Stop its owned session first")
    subprocess.run(["codesign", "--verify", "--strict", str(app)], check=True, timeout=10)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    save(output / "challenge.json", item)
    session = {"schemaVersion": 1, "target": name, "binarySHA256": digest,
               "challengeID": item["challengeID"], "startURL": item["startURL"],
               "startedAt": datetime.now(timezone.utc).isoformat(), "maximumSessionSeconds": seconds,
               "log": str(output / "browser.log"), "stopFile": str(output / "stop"),
               "assessment": "requires-independent-review", "pageStateObservedByRunner": False,
               "humanSetupVerified": False, "systemInputPostedByRunner": False, "status": "preflight"}
    launcher = None
    pid = None

    def interrupted(_number, _frame):
        raise SystemExit("The bounded website session stopped")

    previous = {number: signal.signal(number, interrupted)
                for number in [signal.SIGTERM, signal.SIGINT, signal.SIGALRM]}
    signal.alarm(seconds + 30)
    try:
        if target == "preview":
            preflight = output / "permission.log"
            preflight_launcher, _ = launch(name, preflight, ["--permissions"])
            try:
                preflight_launcher.wait(timeout=15)
            finally:
                if not stop(preflight_launcher, binary):
                    raise RuntimeError("The permission preflight did not stop")
            if "DEVICE_KEYBOARD permission=true" not in preflight.read_text():
                raise RuntimeError("Existing preview Input Monitoring is ineffective. No grant was requested")
        launcher, _ = launch(name, Path(session["log"]), ["--url", item["startURL"]])
        pid = ready(Path(session["log"]), r"Browser ready: pid=(\d+)")
        session.update(pid=pid, launcherPID=launcher.pid, status="running")
        if not process_matches(pid, binary):
            raise RuntimeError("The research process changed")
        if target == "preview" and "DEVICE_KEYBOARD permission=true openStatus=0" not in Path(session["log"]).read_text():
            raise RuntimeError("The preview keyboard reader is unavailable")
        save(output / "session.json", session)
        (output / "AGENT-TASK.md").write_text(instructions(item, session))
        save(output / "attempt-template.json", {
            "challengeID": item["challengeID"], "targetPID": pid, "binarySHA256": digest,
            "phase": "cold-start", "agent": "", "route": "", "steps": [], "elapsedSeconds": None,
            "referenceSession": None, "referenceOutcome": "not-tested", "humanSetupEvidence": None,
            "claimedOutcome": "not-tested", "evidencePaths": [], "limitations": [],
            "assessment": "requires-independent-review"})
        print(json.dumps({"ready": True, "pid": pid, "task": str(output / "AGENT-TASK.md"),
                          "session": str(output / "session.json"), "challenge": item}), flush=True)
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not (output / "stop").exists():
            if not process_matches(pid, binary):
                session["status"] = "browser-exited"
                break
            time.sleep(.25)
        else:
            session["status"] = "stopped" if (output / "stop").exists() else "expired"
    except BaseException as error:
        session.update(status="interrupted" if isinstance(error, SystemExit) else "failed", error=str(error))
        raise
    finally:
        session["ownedHostStopped"] = stop(launcher, binary, pid)
        signal.alarm(0)
        for number, handler in previous.items():
            signal.signal(number, handler)
        session["endedAt"] = datetime.now(timezone.utc).isoformat()
        save(output / "session.json", session)
        if not session["ownedHostStopped"]:
            raise RuntimeError("The owned research browser did not stop")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=TARGETS, default="preview")
    parser.add_argument("--site", choices=SITES, default="google")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--challenge", type=Path, help="Reuse the exact task for a matched reference")
    args = parser.parse_args()
    run(args.target, args.site, args.output, args.seconds, args.challenge)
