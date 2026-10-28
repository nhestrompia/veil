"""Build a separate research browser using the pinned stable-activity engine."""

import hashlib
import argparse
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile

from engine_runtime import BASE, engine_environment
from run_native import ROOT
from process_cleanup import matching_pids

MANIFEST = ROOT / 'docs/evidence/focus-engine-browser-manifest.json'
TARGETS = {
    'AgentFreeBrowserEngine': ('dist', 'research.agentfreebrowser.focusengine', []),
    'FocusEngineNativeControl': ('.build', 'research.agentfreebrowser.focusengine.nativecontrol',
                                 ['BROWSER_NAVIGATION_CONTROL', 'FOCUS_ENGINE_NATIVE_CONTROL']),
    'FocusEngineStableControl': ('.build', 'research.agentfreebrowser.focusengine.stablecontrol',
                                 ['BROWSER_NAVIGATION_CONTROL']),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engine_pins(root):
    pins = {}
    for framework in root.glob('*.framework'):
        binary = (framework / framework.stem).resolve()
        if binary.is_file():
            pins[str(binary.relative_to(root))] = digest(binary)
    for binary in root.glob('*.dylib'):
        resolved = binary.resolve()
        pins[str(resolved.relative_to(root))] = digest(resolved)
    helpers = root / 'WebKit.framework/XPCServices'
    for app in helpers.glob('*.xpc'):
        info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
        binary = (app / 'Contents/MacOS' / info['CFBundleExecutable']).resolve()
        pins[str(binary.relative_to(root))] = digest(binary)
    if not any('/MacOS/com.apple.WebKit.WebContent' in name for name in pins):
        raise RuntimeError('The engine has no pinned content helper')
    return dict(sorted(pins.items()))


def replaceable(previous, paths):
    if any(previous.get(key) is not False for key in ['permissionApproved', 'permissionRequested', 'effectiveGrantConfirmed']):
        raise RuntimeError('A requested or approved consent image cannot be replaced')
    for name, path in paths.items():
        binary = path / 'Contents/MacOS' / name
        if (previous['targets'][name]['path'] != str(path)
                or digest(binary) != previous['targets'][name]['binarySHA256'] or matching_pids(binary)):
            raise RuntimeError('The ungranted image changed or is running')


def build(replace_ungranted=False):
    root = (BASE / 'output/Release').resolve()
    engine_environment(root)
    pins = engine_pins(root)
    paths = {name: ROOT / parent / (name + '.app') for name, (parent, _, _) in TARGETS.items()}
    previous = None
    if MANIFEST.exists() or any(path.exists() for path in paths.values()):
        if not replace_ungranted or not MANIFEST.exists():
            raise RuntimeError('Refuse to overwrite a built or permissioned focus-browser image')
        previous = json.loads(MANIFEST.read_text())
        replaceable(previous, paths)
    sources = sorted((ROOT / 'Sources/Browser').glob('*.swift')) + [
        ROOT / 'Sources/Diagnostics/EngineRuntime.swift',
        ROOT / 'Sources/EngineBrowser/FocusEngineRuntime.swift']
    module_cache = ROOT / '.build/module-cache'
    module_cache.mkdir(parents=True, exist_ok=True)
    report = {'engineRoot': str(root), 'engineSHA256': pins, 'targets': {},
              'permission': 'macOS Input Monitoring / ListenEvent', 'permissionApproved': False,
              'permissionRequested': False, 'effectiveGrantConfirmed': False,
              'engineBundled': False, 'hardenedRuntime': False,
              'launchRequirement': 'Native app bootstrap or tools/launch_focus_browser.py; workspace research engine required',
              'sourceHashes': {str(path.relative_to(ROOT)): digest(path) for path in sources}}
    with tempfile.TemporaryDirectory(prefix='focus-engine-build-', dir=ROOT / '.build') as directory:
        staging = Path(directory)
        generated = staging / 'FocusEnginePins.swift'
        generated.write_text('enum FocusEnginePins {\n    static let root = ' + json.dumps(str(root))
                             + '\n    static let hashes: [String: String] = [\n'
                             + ''.join('        ' + json.dumps(name) + ': ' + json.dumps(value) + ',\n'
                                       for name, value in pins.items()) + '    ]\n}\n')
        for name, (_, identifier, flags) in TARGETS.items():
            app = staging / (name + '.app')
            binary = app / 'Contents/MacOS' / name
            binary.parent.mkdir(parents=True)
            defines = ['DEVICE_KEYBOARD_EXPERIMENT', 'INTEGRATED_BROWSER', 'STABLE_ENGINE_BROWSER', *flags]
            command = ['xcrun', 'swiftc', '-swift-version', '6', '-warnings-as-errors', '-parse-as-library',
                       '-O', '-target', 'arm64-apple-macosx26.6', '-module-cache-path', str(module_cache)]
            for define in defines:
                command += ['-D', define]
            extra = [] if name == 'AgentFreeBrowserEngine' else [
                ROOT / 'Sources/Diagnostics/FocusEngineControl.swift',
                ROOT / 'Sources/Diagnostics/DiagnosticSecureInput.swift']
            subprocess.run([*command, *map(str, sources + extra), str(generated), '-o', str(binary)],
                           check=True, timeout=120)
            info = {'CFBundleIdentifier': identifier, 'CFBundleName': name, 'CFBundleExecutable': name,
                    'CFBundlePackageType': 'APPL', 'LSMinimumSystemVersion': '26.6',
                    'NSHighResolutionCapable': True,
                    'NSInputMonitoringUsageDescription':
                    'Route the measured built-in keyboard while this research browser is foreground. No typed text or key codes enter logs.',
                    'NSAppTransportSecurity': {'NSAllowsLocalNetworking': True}}
            (app / 'Contents/Info.plist').write_bytes(plistlib.dumps(info))
            subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True, timeout=15)
            subprocess.run(['codesign', '--verify', '--strict', str(app)], check=True, timeout=15)
            report['targets'][name] = {'path': str(paths[name]), 'bundleIdentifier': identifier,
                                       'binarySHA256': digest(binary), 'defines': defines,
                                       'diagnosticInput': name != 'AgentFreeBrowserEngine'}
        activation_pins = staging / 'FocusActivationPins.swift'
        targets = [(row['bundleIdentifier'], row['path'] + '/Contents/MacOS/' + name, row['binarySHA256'])
                   for name, row in report['targets'].items()]
        targets.append(('research.agentfreebrowser.control',
                        str(ROOT / 'dist/InspectableControl.app/Contents/MacOS/InspectableControl'),
                        'ac6b5b199ebfeafbeb53b85ad759c966bbd4f9b852cfc39ecd89af6b725bab36'))
        activation_pins.write_text('enum FocusActivationPins {\n    static let targets: [(String, String, String)] = [\n'
                                  + ''.join('        (' + ', '.join(json.dumps(value) for value in row) + '),\n'
                                            for row in targets) + '    ]\n}\n')
        helper = staging / 'FocusEngineActivation'
        subprocess.run(['xcrun', 'swiftc', '-swift-version', '6', '-warnings-as-errors', '-parse-as-library', '-O',
                        '-module-cache-path', str(module_cache),
                        str(ROOT / 'Sources/Diagnostics/FocusEngineActivation.swift'), str(activation_pins),
                        '-o', str(helper)], check=True, timeout=60)
        report['activationHelperSHA256'] = digest(helper)
        if previous is not None:
            replaceable(previous, paths)
            backup = Path(tempfile.mkdtemp(prefix='focus-engine-ungranted-backup-', dir=ROOT / '.build'))
            for name, path in paths.items():
                path.rename(backup / (name + '.app'))
            MANIFEST.rename(backup / 'manifest.json')
        for name in TARGETS:
            (staging / (name + '.app')).rename(paths[name])
        helper.replace(ROOT / '.build/FocusEngineActivation')
    report['sourceHashes'].update({
        name: digest(ROOT / name) for name in ['tools/build_focus_browser.py',
        'Sources/Diagnostics/FocusEngineControl.swift', 'Sources/Diagnostics/DiagnosticSecureInput.swift',
        'Sources/Diagnostics/FocusEngineActivation.swift']})
    MANIFEST.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'manifest': str(MANIFEST), 'targets': report['targets']}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--replace-ungranted', action='store_true')
    args = parser.parse_args()
    build(args.replace_ungranted)
