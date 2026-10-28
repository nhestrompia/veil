"""Compare read-only AX and window captures on a physically tested Veil session."""

import argparse
import hashlib
import json
from pathlib import Path

from pointer_attempt_review import review
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import Oracle, probe


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def run(session_path, output):
    session = json.loads(session_path.read_text())
    active(session)
    physical = json.loads(session_path.with_name('physical-control.json').read_text())
    if (session['target'] != 'Veil' or session['fixtureSurface'] != 'physical-mouse'
            or physical['pid'] != session['pid']
            or physical['binarySHA256'] != session['binarySHA256']
            or physical['userResponse'] != 'Click recorded and wheel scrolls'
            or sum(item['accepted'] for item in physical['state']['submissions']) != 1):
        raise RuntimeError('Need this exact Veil physical mouse control')
    root = Path(__file__).resolve().parent.parent
    output = output.resolve()
    if not output.is_relative_to(root / 'artifacts'):
        raise ValueError('Use a fresh project artifact directory')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    oracle = Oracle(session['controller'])
    before = oracle.state(session['trial'])
    log = Path(session['log'])
    offset = len(log.read_text())
    report = {'binarySHA256': session['binarySHA256'], 'pid': session['pid'],
              'scope': 'Read-only app AX and target-window captures; no input or display-wide capture',
              'candidateScrollPosition': [e['y'] for e in before['events'] if e['type'] == 'scroll'][-1:],
              'results': []}
    report['permissions'] = probe(['permissions'], output / 'permissions.json', background=True)
    reference = None

    def observe(pid, trial, route, prefix):
        result = {'pid': pid, 'route': route}
        marker = oracle.state(trial)['secret']
        if route == 'ax':
            data = probe(['ax', pid], prefix.with_suffix('.ax.json'), background=True)
            text = json.dumps(data)
            result.update(elements=len(data.get('elements', [])),
                          pageButtonExposed='Record physical click' in text,
                          markerExposed=marker in text,
                          error=data.get('error'))
        else:
            image = prefix.with_suffix('.png')
            data = probe([route, pid, image], prefix.with_suffix('.capture.json'), background=True)
            result['capture'] = data
            if data.get('status') == 'captured':
                result['imageSHA256'] = hashlib.sha256(image.read_bytes()).hexdigest()
                ocr = probe(['ocr', image], prefix.with_suffix('.ocr.json'), background=True)
                text = json.dumps(ocr)
                result.update(ocrAvailable='text' in ocr,
                              ocrTextCount=len(ocr.get('text', [])),
                              markerExposed=marker in text,
                              fixtureTextExposed=any(phrase.lower() in text.lower() for phrase in
                                  ['Record physical click', 'Veil physical mouse control',
                                   'Wheel control complete', 'No click recorded']))
            result['markerInterpretation'] = 'Candidate marker is offscreen after physical scrolling; absence alone proves nothing'
        return result

    try:
        reference = prepare('InspectableControl', output / 'reference', oracle)
        report['reference'] = {'pid': reference['pid'], 'binarySHA256': reference['binarySHA256']}
        for route in ['ax', 'capture', 'display-capture', 'system-capture']:
            control = observe(reference['pid'], reference['trial'], route, output / (route + '-reference'))
            active(session)
            candidate = observe(session['pid'], session['trial'], route, output / (route + '-veil'))
            report['results'].append({'route': route, 'control': control, 'candidate': candidate})
            save(output / 'results.json', report)
    finally:
        if reference is not None:
            close(reference)
            report['referenceStopped'] = True
        active(session)
        after = oracle.state(session['trial'])
        save(output / 'oracle-after.json', after)
        report['interactionReview'] = review(before, after, log.read_text()[offset:])
        save(output / 'results.json', report)
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.session, args.output)
