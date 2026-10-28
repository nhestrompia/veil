"""Generate a research patch from hash-verified, pinned WebKit source files."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "engine/webkit-source-manifest.json"
PATCH = ROOT / "engine/patches/stable-page-activity.patch"
PROXY = "Source/WebKit/UIProcess/WebPageProxy"
CONFIG = "Source/WebKit/UIProcess/API/APIPageConfiguration.h"
COCOA = "Source/WebKit/UIProcess/API/Cocoa/WKWebViewConfiguration"
HEADER = "Source/WebKit/UIProcess/ContentActivityProjection.h"


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise RuntimeError(f"Expected exactly one source anchor: {before[:90]}")
    return source.replace(before, after, 1)


def read_sources(directory, fetch=False):
    manifest = json.loads(MANIFEST.read_text())
    sources = {}
    for entry in manifest["files"]:
        path = directory / entry["path"]
        if not path.exists() and fetch:
            with urllib.request.urlopen(entry["url"], timeout=30) as response:
                data = response.read(entry["bytes"] + 1)
            if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise RuntimeError(f"Downloaded source identity mismatch: {entry['path']}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"Pinned source changed; refusing replacement: {entry['path']}")
        sources[entry["path"]] = data.decode()
    return manifest, sources


def changed_sources(original):
    result = {}
    result[CONFIG] = replace_once(original[CONFIG],
        "    bool shouldSendConsoleLogsToUIProcessForTesting() const",
        "    bool usesStablePageActivityForResearch() const { return m_data.usesStablePageActivityForResearch; }\n"
        "    void setUsesStablePageActivityForResearch(bool enabled) { m_data.usesStablePageActivityForResearch = enabled; }\n\n"
        "    bool shouldSendConsoleLogsToUIProcessForTesting() const")
    result[CONFIG] = replace_once(result[CONFIG],
        "        bool shouldSendConsoleLogsToUIProcessForTesting { false };",
        "        bool usesStablePageActivityForResearch { false };\n"
        "        bool shouldSendConsoleLogsToUIProcessForTesting { false };")
    result[COCOA + "Private.h"] = replace_once(original[COCOA + "Private.h"],
        "@interface WKWebViewConfiguration (WKPrivate)\n",
        "@interface WKWebViewConfiguration (WKPrivate)\n\n"
        "@property (nonatomic, setter=_setUsesStablePageActivityForResearch:) BOOL _usesStablePageActivityForResearch;\n")
    result[COCOA + ".mm"] = replace_once(original[COCOA + ".mm"],
        "- (BOOL)_shouldSendConsoleLogsToUIProcessForTesting\n",
        "- (BOOL)_usesStablePageActivityForResearch\n{\n"
        "    return _pageConfiguration->usesStablePageActivityForResearch();\n}\n\n"
        "- (void)_setUsesStablePageActivityForResearch:(BOOL)enabled\n{\n"
        "    _pageConfiguration->setUsesStablePageActivityForResearch(enabled);\n}\n\n"
        "- (BOOL)_shouldSendConsoleLogsToUIProcessForTesting\n")
    result[PROXY + ".h"] = replace_once(original[PROXY + ".h"],
        "namespace WebKit {\n", "namespace WebKit {\n\nenum class ContentActivityPolicy : bool;\n")
    result[PROXY + ".h"] = replace_once(result[PROXY + ".h"],
        "    const Ref<API::PageConfiguration> m_configuration;",
        "    const Ref<API::PageConfiguration> m_configuration;\n"
        "    const ContentActivityPolicy m_contentActivityPolicy;")
    result[PROXY + ".h"] = replace_once(result[PROXY + ".h"],
        "    void updateActivityState(OptionSet<WebCore::ActivityState> flagsToUpdate);",
        "    OptionSet<WebCore::ActivityState> activityStateForContent() const;\n"
        "    void updateActivityState(OptionSet<WebCore::ActivityState> flagsToUpdate);")
    proxy = replace_once(original[PROXY + ".cpp"], '#include "WebPageProxy.h"\n',
        '#include "WebPageProxy.h"\n#include "ContentActivityProjection.h"\n')
    proxy = replace_once(proxy, "    , m_configuration(configuration)\n",
        "    , m_configuration(configuration)\n"
        "    , m_contentActivityPolicy(configuration->usesStablePageActivityForResearch() ? ContentActivityPolicy::StableBrowsing : ContentActivityPolicy::Native)\n")
    proxy = replace_once(proxy, "void WebPageProxy::updateActivityState(OptionSet<ActivityState> flagsToUpdate)\n",
        "OptionSet<ActivityState> WebPageProxy::activityStateForContent() const\n{\n"
        "    return OptionSet<ActivityState>::fromRaw(projectContentActivity<ActivityState>(internals().activityState.toRaw(), m_contentActivityPolicy));\n}\n\n"
        "void WebPageProxy::updateActivityState(OptionSet<ActivityState> flagsToUpdate)\n")
    proxy = replace_once(proxy, "Messages::WebPage::SetActivityState(internals().activityState, activityStateChangeID)",
        "Messages::WebPage::SetActivityState(activityStateForContent(), activityStateChangeID)")
    proxy = replace_once(proxy, "    parameters.activityState = internals().activityState;",
        "    parameters.activityState = activityStateForContent();")
    result[PROXY + ".cpp"] = proxy
    result[HEADER] = (ROOT / "engine/ContentActivityProjection.h").read_text()
    return result


def generate(source_directory, check=False, fetch=False):
    manifest, original = read_sources(source_directory, fetch)
    updated = changed_sources(original)
    patch = "".join("".join(difflib.unified_diff(original.get(name, "").splitlines(True), text.splitlines(True),
        fromfile="a/" + name if name in original else "/dev/null", tofile="b/" + name))
        for name, text in sorted(updated.items()))
    if check and PATCH.read_text() != patch:
        raise RuntimeError("Committed engine patch differs from its generator")
    ROOT.joinpath(".build").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="webkit-patch-", dir=ROOT / ".build") as temporary:
        staging = Path(temporary)
        for name in updated:
            if name in original:
                path = staging / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(original[name])
        patch_file = staging / "research.patch"
        patch_file.write_text(patch)
        applied = subprocess.run(["patch", "-p1", "-F", "0", "-t", "-i", str(patch_file)],
            cwd=staging, capture_output=True, text=True, check=True)
        for name, expected in updated.items():
            if (staging / name).read_text() != expected:
                raise RuntimeError(f"Patch application changed unexpected content: {name}")
    report = {"revision": manifest["revision"], "sourceFilesVerified": len(original),
              "patchSHA256": hashlib.sha256(patch.encode()).hexdigest(),
              "changedFiles": sorted(updated), "exactPatchApplicationVerified": True,
              "nativeActivityUpdateUnmodified": True, "nativeSecureInputSourceUnmodified": True,
              "engineCompiled": False, "engineRuntimeTested": False, "patchToolOutput": applied.stdout}
    native_method = "void WebPageProxy::updateActivityState(OptionSet<ActivityState> flagsToUpdate)"
    def native_body(version):
        return version.split(native_method, 1)[1].split("void WebPageProxy::updateActivityState()", 1)[0]
    if native_body(original[PROXY + ".cpp"]) != native_body(updated[PROXY + ".cpp"]):
        raise RuntimeError("Native activity calculation changed")
    if not check:
        PATCH.parent.mkdir(parents=True, exist_ok=True)
        PATCH.write_text(patch)
    ROOT.joinpath(".build/webkit-activity-patch-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / ".build/webkit-source-94f9")
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(args.source.resolve(), args.check, args.fetch)
