"""Check local pointer dispatch through the pinned engine, without hardware or OS input."""

import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess

from launch_focus_browser import verified_target
from run_native import ROOT


def run(output, veil=False):
    _, environment = verified_target()
    binary = ROOT / ('.build/veil-mouse-webkit-tests' if veil else '.build/hardware-pointer-webkit-tests')
    sources = ['Sources/Browser/AXBoundary.swift', 'Sources/Browser/RestrictedWebView.swift',
               'Sources/Browser/DeviceKeyboard.swift', 'Sources/Browser/HIDSourcePolicy.swift',
               'Sources/Browser/HIDPointerPolicy.swift', 'Sources/Browser/DevicePointer.swift',
               'Sources/Browser/BrowserRuntimePolicy.swift', 'Sources/Diagnostics/EngineRuntime.swift',
               'Tests/VeilMouseWebKitTests.swift' if veil else 'Tests/HardwarePointerWebKitTests.swift']
    subprocess.run(['xcrun', 'swiftc', '-swift-version', '6', '-warnings-as-errors', '-parse-as-library',
                    '-D', 'DEVICE_KEYBOARD_EXPERIMENT', '-D', 'DEVICE_POINTER_EXPERIMENT',
                    *(['-D', 'VEIL_BROWSER'] if veil else []),
                    '-module-cache-path', str(ROOT / '.build/module-cache'),
                    *[str(ROOT / name) for name in sources], '-o', str(binary)], check=True, timeout=60)
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a fresh project artifact directory')
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'control.log').open('w') as stream:
        completed = subprocess.run([str(binary)], env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=25)
    text = (output / 'control.log').read_text()
    delivered = 'VEIL_MOUSE_CONTROL passed=true' in text if veil else 'WEBKIT_POINTER_CONTROL {"clicks":1' in text
    result = {'exitCode': completed.returncode, 'clickDelivered': delivered,
              'wheelAndNativeControlDelivered': delivered if veil else None,
              'controlOnly': True, 'physicalInputVerified': False, 'externalAttack': False}
    (output / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    print(text)
    if completed.returncode or not result['clickDelivered']:
        raise RuntimeError('Pointer WebKit dispatch control failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/hardware-pointer-154' /
                        ('webkit-control-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--veil', action='store_true')
    args = parser.parse_args()
    run(args.output, args.veil)
