"""Build a separate, ungranted hardware-pointer candidate without replacing tested apps."""

import json
import argparse
from pathlib import Path
import plistlib
import subprocess
import tempfile

from build_focus_browser import digest, engine_pins
from launch_focus_browser import verified_target
from run_native import ROOT
from process_cleanup import matching_pids

NAME = 'AgentFreeBrowserPointer'
APP = ROOT / 'dist' / (NAME + '.app')
MANIFEST = ROOT / 'docs/evidence/hardware-pointer-browser-manifest.json'


def replaceable(name=NAME, app_path=APP, manifest_path=MANIFEST):
    previous = json.loads(manifest_path.read_text())
    binary = app_path / 'Contents/MacOS' / name
    if (any(previous.get(key) is not False for key in
            ['permissionApproved', 'permissionRequested', 'effectiveGrantConfirmed'])
            or previous['targets'][name]['binarySHA256'] != digest(binary)
            or previous['targets'][name]['path'] != str(app_path) or matching_pids(binary)):
        raise RuntimeError('Refuse to replace an approved, changed, or running candidate')


def build(replace_ungranted=False, *, name=NAME, app_path=APP, manifest_path=MANIFEST,
          identifier='research.agentfreebrowser.pointer', extra_defines=()):
    replacing = app_path.exists() or manifest_path.exists()
    if replacing:
        if not replace_ungranted or not manifest_path.exists():
            raise RuntimeError('Refuse to overwrite a built hardware-pointer candidate')
        replaceable(name, app_path, manifest_path)
    _, environment = verified_target()
    root = Path(environment['AFB_RESEARCH_FRAMEWORK_ROOT'])
    pins = engine_pins(root)
    sources = sorted((ROOT / 'Sources/Browser').glob('*.swift')) + [
        ROOT / 'Sources/Diagnostics/EngineRuntime.swift',
        ROOT / 'Sources/EngineBrowser/FocusEngineRuntime.swift']
    defines = ['DEVICE_KEYBOARD_EXPERIMENT', 'INTEGRATED_BROWSER', 'STABLE_ENGINE_BROWSER', 'DEVICE_POINTER_EXPERIMENT']
    defines += list(extra_defines)
    with tempfile.TemporaryDirectory(prefix='hardware-pointer-build-', dir=ROOT / '.build') as directory:
        staging = Path(directory)
        generated = staging / 'FocusEnginePins.swift'
        generated.write_text('enum FocusEnginePins {\n    static let root = ' + json.dumps(str(root))
                             + '\n    static let hashes: [String: String] = [\n'
                             + ''.join('        ' + json.dumps(name) + ': ' + json.dumps(value) + ',\n'
                                       for name, value in pins.items()) + '    ]\n}\n')
        app = staging / app_path.name
        binary = app / 'Contents/MacOS' / name
        binary.parent.mkdir(parents=True)
        command = ['xcrun', 'swiftc', '-swift-version', '6', '-warnings-as-errors', '-parse-as-library',
                   '-O', '-target', 'arm64-apple-macosx26.6', '-module-cache-path', str(ROOT / '.build/module-cache')]
        for define in defines:
            command += ['-D', define]
        subprocess.run([*command, *map(str, sources), str(generated), '-o', str(binary)], check=True, timeout=120)
        info = {'CFBundleIdentifier': identifier, 'CFBundleName': name, 'CFBundleExecutable': name,
                'CFBundlePackageType': 'APPL', 'LSMinimumSystemVersion': '26.6', 'NSHighResolutionCapable': True,
                'NSInputMonitoringUsageDescription':
                'Route the measured keyboard and relative mouse while this research browser has focus. No input contents enter logs.',
                'NSAppTransportSecurity': {'NSAllowsLocalNetworking': True}}
        (app / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
        subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True, timeout=15)
        subprocess.run(['codesign', '--verify', '--strict', str(app)], check=True, timeout=15)
        record = {'engineRoot': str(root), 'engineSHA256': pins,
                  'targets': {name: {'path': str(app_path), 'bundleIdentifier': identifier,
                                     'binarySHA256': digest(binary), 'defines': defines, 'diagnosticInput': False}},
                  'permission': 'macOS Input Monitoring / ListenEvent', 'permissionApproved': False,
                  'permissionRequested': False, 'effectiveGrantConfirmed': False,
                  'physicalMouseControlVerified': False, 'liveAttacksVerified': False,
                  'engineBundled': False, 'hardenedRuntime': False,
                  'sourceHashes': {str(path.relative_to(ROOT)): digest(path) for path in sources},
                  'pointerScope': 'Measured relative devices, application-owned pointer, primary webpage clicks only. No drag, scroll, double click, or native toolbar clicks.'}
        if 'VEIL_BROWSER' in extra_defines:
            record.update(pointerScope='Measured relative devices authorize primary clicks, hover, and vertical wheel input at the standard cursor. Automatic device activation. No drag, secondary/double clicks, or trackpad gestures.',
                          coordinateRedirectionLimitAccepted=True, physicalWheelControlVerified=False,
                          physicalMouseControlVerified=False)
        if replacing:
            replaceable(name, app_path, manifest_path)
            backup = Path(tempfile.mkdtemp(prefix='hardware-pointer-ungranted-backup-', dir=ROOT / '.build'))
            app_path.rename(backup / app_path.name)
            manifest_path.rename(backup / 'manifest.json')
        app.rename(app_path)
        manifest_path.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'manifest': str(manifest_path), 'target': record['targets'][name]}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replace-ungranted', action='store_true')
    build(parser.parse_args().replace_ungranted)
