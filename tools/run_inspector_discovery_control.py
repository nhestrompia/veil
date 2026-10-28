"""Calibrate private Cocoa inspector discovery on one disposable readable control."""

import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import threading

from fixture import FixtureServer
from process_cleanup import matching_pids, stop_launched
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle


def verified_bundle(binary):
    manifest = json.loads((ROOT / "docs/evidence/inspector-discovery-app-manifest.json").read_text())
    app = binary.parents[2]
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    if (str(app) != manifest["path"] or binary.resolve() != binary
            or info["CFBundleIdentifier"] != "research.agentfreebrowser.inspectordiscovery"
            or hashlib.sha256(binary.read_bytes()).hexdigest() != manifest["executableSHA256"]):
        raise RuntimeError("The pinned discovery comparison app changed")
    for name, digest in manifest["sourceHashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("A pinned discovery comparison source changed")
    subprocess.run(["codesign", "--verify", "--strict", str(app)],
                   check=True, capture_output=True, timeout=10)


def invoke_bundle(arguments, output, binary):
    stdout = output / "helper.stdout"
    launcher = subprocess.Popen(["open", "-g", "-n", "-W", str(binary.parents[2]),
                                 "--stdout", str(stdout), "--stderr", "/dev/null", "--args", *arguments],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = set()
    try:
        launcher.wait(timeout=18)
        return json.loads(stdout.read_text()), launcher.returncode
    finally:
        cleaned = stop_launched(launcher, binary)
        if launcher.poll() is None:
            launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait()
        if not cleaned:
            raise RuntimeError("The bundled discovery helper did not stop")


def run(output, fetch_listing=False, register_and_list=False, appkit=False, bundled=False):
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A readable reference already exists")
    binary = ROOT / ("dist/InspectorDiscoveryControl.app/Contents/MacOS/InspectorDiscoveryControl"
                     if bundled else ".build/inspector-discovery-control")
    if not binary.is_file():
        raise RuntimeError("Build the inspector discovery control first")
    if matching_pids(binary):
        raise RuntimeError("A discovery helper already exists")
    if bundled:
        verified_bundle(binary)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {"status": "inconclusive", "candidateLaunched": False, "inputPosted": False,
              "launchMode": "app-bundle" if bundled else "executable", "helperPath": str(binary),
              "helperSHA256": hashlib.sha256(binary.read_bytes()).hexdigest()}
    server = FixtureServer(("127.0.0.1", 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    reference = None
    try:
        worker.start()
        controller = output / "fixture-controller.json"
        controller.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
        controller.chmod(0o600)
        oracle = Oracle(controller)
        reference = prepare("InspectableControl", output / "reference", oracle)
        report["referencePID"] = reference["pid"]
        command = [str(binary), str(reference["pid"]), reference["trial"]["url"]]
        if register_and_list:
            command.append("--register-and-list")
        elif fetch_listing:
            command.append("--fetch-listing")
        if appkit:
            command.append("--appkit")
        if bundled:
            report["discovery"], report["launcherExitCode"] = invoke_bundle(command[1:], output, binary)
        else:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=18)
            report["helperStderrCharacters"] = len(completed.stderr)
            report["helperExitCode"] = completed.returncode
            if completed.returncode == 0:
                report["discovery"] = json.loads(completed.stdout)
        report["helperCleanupVerified"] = True
        report["submissions"] = oracle.state(reference["trial"])["submissions"]
        if report["submissions"]:
            raise RuntimeError("Discovery unexpectedly submitted a task")
    except Exception as error:
        report["error"] = str(error)
    finally:
        try:
            if reference is not None:
                close(reference)
                report["referenceCleanupVerified"] = True
        finally:
            if worker.is_alive():
                server.shutdown()
            server.server_close()
            if worker.ident is not None:
                worker.join(timeout=3)
            report["fixtureStopped"] = not worker.is_alive()
            if (report.get("discovery", {}).get("status") == "reference-discovered"
                    and "error" not in report and report.get("referenceCleanupVerified") is True
                    and report.get("helperCleanupVerified") is True
                    and report["fixtureStopped"] and report.get("submissions") == []):
                report["status"] = "reference-discovered"
            (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["fixtureStopped"]:
        raise RuntimeError("The local fixture did not stop")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--fetch-listing", action="store_true")
    mode.add_argument("--register-and-list", action="store_true")
    parser.add_argument("--appkit", action="store_true")
    parser.add_argument("--bundled", action="store_true")
    args = parser.parse_args()
    report = run(args.output, args.fetch_listing, args.register_and_list, args.appkit, args.bundled)
    print(json.dumps(report))
    raise SystemExit(0 if report["status"] == "reference-discovered" else 1)
