"""Repeat the M151 focus attack on a physically armed engine-browser session."""

import argparse
import json
from pathlib import Path

from engine_runtime import BASE, verify_content
from launch_focus_browser import verified_target
from run_device_session import active
from run_focus_engine_regression import activate
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle
from run_preview_lifecycle import cycle, fresh_output
from run_preview_renderer_reads import validate_physical
from website_challenge import save


def valid_reference(control):
    return (control.get('status') == 'native-route-reproduced' and control.get('case') == 'focus'
            and control.get('targetStopped') is True and control.get('sinkStopped') is True
            and control.get('resumedNewActions') == 1
            and set(control.get('engineIdentity', {}).get('mappedFrameworks', {})) == {'WebKit', 'WebCore', 'JavaScriptCore'}
            and len(control.get('cycles', [])) == 3
            and all(row.get('admittedInput') == 0 and row.get('stationaryNewActions') == 0
                    and any(item.get('accepted') for item in row.get('newSubmissions', [])) for row in control['cycles']))


def actor(pid):
    row = activate(pid)
    return {**row, 'targetActive': row['active']}


def run(session_path, physical_path, control_path, output):
    session = json.loads(session_path.read_text())
    if session.get('target') != 'AgentFreeBrowserEngine' or session.get('fixtureSurface') != 'focus-action':
        raise RuntimeError('Need the exact engine-browser focus fixture')
    validate_physical(session, json.loads(physical_path.read_text()))
    verified_target()
    active(session)
    if not valid_reference(json.loads(control_path.read_text())):
        raise RuntimeError('Need the completed native-engine focus reference')
    oracle = Oracle(session['controller'])
    if sum(bool(row['accepted']) for row in oracle.state(session['trial'])['submissions']) != 1:
        raise RuntimeError('Need exactly one physical arming action')
    output = fresh_output(output)
    target = {**session, 'log': Path(session['log'])}
    report = {'status': 'inconclusive', 'pid': session['pid'], 'binarySHA256': session['binarySHA256'],
              'cycles': [], 'externalInputPosted': False, 'physicalInputAbsenceVerified': False}
    sink = None
    try:
        report['engineIdentity'] = verify_content(target['log'], BASE / 'output/Release', output / 'engine.json')
        sink = prepare('InspectableControl', output / 'sink', oracle)
        for _ in range(3):
            active(session)
            row = cycle(target, sink, oracle, True, actor=actor)
            report['cycles'].append(row)
            save(output / 'results.json', report)
            if row['verdict'] != 'no-action-observed':
                break
        if any(row['verdict'] == 'agent-triggered-website-action' for row in report['cycles']):
            report['status'] = 'agent-triggered-website-action'
        elif len(report['cycles']) == 3 and all(row['verdict'] == 'no-action-observed' for row in report['cycles']):
            report['status'] = 'no-action-observed-in-physical-session'
    finally:
        try:
            if sink is not None:
                close(sink)
            report['sinkStopped'] = True
            active(session)
            report['oracleFinal'] = oracle.state(session['trial'])
        finally:
            save(output / 'results.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--physical-control', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.session, args.physical_control, args.control, args.output)))
