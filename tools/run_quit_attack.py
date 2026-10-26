"""Compare graceful quit actions on disposable local research pages."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_focus_attack import accepted
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_keyboard_observation import secure_input_enabled


def quit_cycle(session, oracle):
    before = oracle.state(session['trial'])
    offset = len(session['log'].read_text())
    process = subprocess.run([str(ROOT / '.build/research-quit'), str(session['pid'])],
                             capture_output=True, text=True, timeout=5, check=True)
    operation = json.loads(process.stdout)
    time.sleep(1)
    after = oracle.state(session['trial'])
    submissions = after['submissions'][len(before['submissions']):]
    tail = session['log'].read_text()[offset:]
    return {'quit': operation, 'newSubmissions': submissions,
            'acceptedInputEvents': tail.count('INPUT_GATE_ACCEPTED'),
            'status': 'autonomous-website-action' if any(row['accepted'] for row in submissions) else 'inconclusive',
            'syntheticInputPosted': False, 'AXCallDuringQuit': False}


def run(output, controller, surface):
    output.mkdir(parents=True, exist_ok=False)
    oracle = Oracle(controller)
    require_input_safety(probe(['permissions'], output / 'permissions.json'))
    binaries = {name: ROOT / f'dist/{name}.app/Contents/MacOS/{name}'
                for name in ['NativeProbe', 'InternalKeyboardControl', 'InspectableControl']}
    binaries['ResearchQuit'] = ROOT / '.build/research-quit'
    if any(matching_pids(binaries[name]) for name in ['InternalKeyboardControl', 'InspectableControl']):
        raise RuntimeError('A disposable research control is already running')
    report = {'surface': surface, 'humanBaseline': False,
              'binarySHA256': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in binaries.items()},
              'status': 'inconclusive'}
    def unchanged():
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != report['binarySHA256'][name]
               for name, path in binaries.items()):
            raise RuntimeError('A quit-test executable changed during comparison')
    reference = candidate = None
    try:
        reference = prepare('InspectableControl', output / 'reference', oracle, f'?surface={surface}')
        report['referenceArming'] = probe(['ax-action', reference['pid']], output / 'reference-arm.json')
        time.sleep(0.3)
        if accepted(oracle.state(reference['trial'])) == 0:
            report['reason'] = 'Readable reference did not arm'
            return
        unchanged()
        report['reference'] = quit_cycle(reference, oracle)
        close(reference)
        reference = None
        report['referenceCleanupVerified'] = True
        if report['reference']['status'] != 'autonomous-website-action':
            report['reason'] = 'Readable reference did not record a quit action'
            return
        candidate = prepare('InternalKeyboardControl', output / 'candidate', oracle, f'?surface={surface}')
        unchanged()
        report['candidate'] = quit_cycle(candidate, oracle)
        report['status'] = report['candidate']['status']
    finally:
        try:
            if candidate:
                close(candidate)
                report['candidateCleanupVerified'] = True
            if reference:
                close(reference)
                report['referenceCleanupVerified'] = True
            report['secureInputAfterCleanup'] = secure_input_enabled()
        finally:
            (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps({'status': report['status'], 'reason': report.get('reason'),
                              'candidate': report.get('candidate')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--controller', type=Path, default=ROOT / 'artifacts/page-feature-controller.json')
    parser.add_argument('--surface', choices=['pagehide-action', 'unload-action'], default='pagehide-action')
    arguments = parser.parse_args()
    run(arguments.output.resolve(), arguments.controller, arguments.surface)
