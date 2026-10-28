"""Build a separate two-target recorder without changing any granted image."""

import argparse
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile

from build_focus_browser import digest
from build_preview_compositor_update import revised_source
from launch_focus_browser import verified_target
from run_native import ROOT
from process_cleanup import matching_pids

MANIFEST = ROOT / 'docs/evidence/engine-compositor-manifest.json'
APP = ROOT / 'dist/EngineCompositorProbe.app'


def build(replace_ungranted=False):
    verified_target()
    if APP.exists() or MANIFEST.exists():
        if not replace_ungranted or not MANIFEST.exists():
            raise RuntimeError('Refuse to replace the pinned engine recorder')
        previous = json.loads(MANIFEST.read_text())
        binary = APP / 'Contents/MacOS/EngineCompositorProbe'
        if (any(previous.get(key) is not False for key in
                ['permissionApproved', 'permissionRequested', 'effectiveGrantConfirmed'])
                or digest(binary) != previous['executableSHA256'] or matching_pids(binary)):
            raise RuntimeError('Only the exact idle unapproved recorder can be replaced')
        backup = Path(tempfile.mkdtemp(prefix='engine-compositor-ungranted-', dir=ROOT / '.build'))
        shutil.copytree(ROOT / '.build/engine-compositor', backup / 'sources')
        APP.rename(backup / APP.name)
        MANIFEST.rename(backup / 'manifest.json')
    engine = json.loads((ROOT / 'docs/evidence/focus-engine-browser-manifest.json').read_text())
    target = engine['targets']['AgentFreeBrowserEngine']
    original_manifest = json.loads((ROOT / 'docs/evidence/preview-compositor-permission-manifest.json').read_text())
    frozen = Path(original_manifest['path']) / 'Contents/MacOS/PreviewCompositorProbe'
    if digest(frozen) != original_manifest['executableSHA256']:
        raise RuntimeError('The existing granted recorder changed')
    folder = ROOT / '.build/engine-compositor'
    folder.mkdir(parents=True, exist_ok=replace_ungranted)
    scope_source = ROOT / 'Sources/Diagnostics/PreviewAXScope.swift'
    scope = scope_source.read_text()
    for old, new in [('AgentFreeBrowserPreview', 'AgentFreeBrowserEngine'),
                     ('research.agentfreebrowser.preview', target['bundleIdentifier']),
                     ('dc3ca62c174d635b9994d9bae27ff6d4dc4a7983bc36d332f720fbbfaf24df70', target['binarySHA256'])]:
        if scope.count(old) != 1:
            raise RuntimeError('The fixed capture scope changed')
        scope = scope.replace(old, new)
    generated_scope = folder / 'EngineCaptureScope.swift'
    generated_scope.write_text(scope)
    original = ROOT / 'Sources/Diagnostics/PreviewCompositorProbe.swift'
    source = revised_source(original.read_text())
    request = '                report["permissionRequested"] = true\n                report["status"] = "requested"\n                report["requestReturned"] = CGRequestScreenCaptureAccess()\n                report["screenRecordingGranted"] = CGPreflightScreenCaptureAccess()'
    if source.count(request) != 1:
        raise RuntimeError('The recorder request branch changed')
    source = source.replace(request, '                throw CompositorFailure("Grant requests require approved System Settings use")')
    call = '                try await run(command: command[0], pid: pid, windowID: windowID, root: root, output: destination, report: &report)'
    if source.count(call) != 1:
        raise RuntimeError('The recorder sequence branch changed')
    source = source.replace(call, '''                if command[0] == "sequence", !EngineCaptureApproval.permits(root: root) {
                    throw CompositorFailure("This exact recorder needs capture approval")
                }
''' + call)
    generated = folder / 'EngineCompositorProbe.swift'
    generated.write_text(source.replace('private enum PreviewCompositorProbe', 'private enum EngineCompositorProbe'))
    approval = folder / 'EngineCaptureApproval.swift'
    approval.write_text('''import Foundation
import CryptoKit

enum EngineCaptureApproval {
    static func permits(root: URL) -> Bool {
        let manifest = root.appendingPathComponent("docs/evidence/engine-compositor-manifest.json")
        guard let data = try? Data(contentsOf: manifest),
              let record = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              record["permissionApproved"] as? Bool == true,
              record["path"] as? String == Bundle.main.bundleURL.resolvingSymlinksInPath().path,
              let expected = record["executableSHA256"] as? String,
              let executable = Bundle.main.executableURL,
              let image = try? Data(contentsOf: executable, options: .mappedIfSafe) else { return false }
        return SHA256.hash(data: image).map { String(format: "%02x", $0) }.joined() == expected
    }
}
''')
    sources = [ROOT / 'Sources/Diagnostics/RendererProcessScope.swift', generated_scope,
               ROOT / 'Sources/Diagnostics/PreviewCompositorPixels.swift',
               ROOT / 'Sources/Diagnostics/PreviewCompositorBackdrop.swift', generated, approval]
    binary = APP / 'Contents/MacOS/EngineCompositorProbe'
    binary.parent.mkdir(parents=True)
    subprocess.run(['xcrun', 'swiftc', '-swift-version', '6', '-warnings-as-errors', '-parse-as-library', '-O',
                    '-target', 'arm64-apple-macosx15.0', '-module-cache-path', str(ROOT / '.build/module-cache'),
                    *map(str, sources), '-o', str(binary)], check=True, timeout=90)
    identifier = 'research.agentfreebrowser.enginecompositor'
    (APP / 'Contents/Info.plist').write_bytes(plistlib.dumps({
        'CFBundleIdentifier': identifier, 'CFBundleName': 'EngineCompositorProbe',
        'CFBundleExecutable': 'EngineCompositorProbe', 'CFBundlePackageType': 'APPL',
        'LSMinimumSystemVersion': '15.0', 'NSHighResolutionCapable': True,
        'NSScreenCaptureUsageDescription': 'Test only the pinned research browser and readable control inside owned opaque coverage. No audio or input.'}))
    subprocess.run(['codesign', '--force', '--sign', '-', '--options', 'runtime', str(APP)], check=True, timeout=15)
    subprocess.run(['codesign', '--verify', '--strict', str(APP)], check=True, timeout=15)
    if digest(frozen) != original_manifest['executableSHA256']:
        raise RuntimeError('The existing recorder changed during build')
    report = {'path': str(APP), 'bundleIdentifier': identifier, 'executableSHA256': digest(binary),
              'sourceHashes': {str(p.relative_to(ROOT)): digest(p) for p in sources},
              'permission': 'macOS Screen Recording', 'permissionApproved': False,
              'permissionRequested': False, 'effectiveGrantConfirmed': False,
              'automaticRequestAtLaunch': False, 'directRequestCommandAvailable': False,
              'maximumSeconds': 25, 'audioCaptured': False, 'inputPosted': False, 'hooksInstalled': False,
              'targetPolicies': [{'name': 'AgentFreeBrowserEngine', 'bundle': target['bundleIdentifier'],
                                  'sha256': target['binarySHA256']},
                                 {'name': 'InspectableControl', 'bundle': 'research.agentfreebrowser.control',
                                  'sha256': 'ac6b5b199ebfeafbeb53b85ad759c966bbd4f9b852cfc39ecd89af6b725bab36'}],
              'scope': 'Only the two exact target images. Unfiltered display / owned-apps / unfiltered display, cropped inside verified opaque owned coverage. Preserve overlap, foreground, geometry, and process identity guards.',
              'originalGrantedRecorderUnchanged': True}
    report['sourceHashes']['tools/build_engine_compositor.py'] = digest(Path(__file__))
    MANIFEST.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'path': str(APP), 'executableSHA256': report['executableSHA256'], 'permissionRequested': False}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--replace-ungranted', action='store_true')
    build(parser.parse_args().replace_ungranted)
