"""Compare unfiltered exclusion updates on the archived physical-test images."""

import argparse
import hashlib
import json
from pathlib import Path

from run_backdrop_metadata import run as trial
from run_compositor_refresh_probe import invoke
from run_native import ROOT

STAGES = ['initial-exclude-helper', 'updated-include-helper', 'updated-exclude-helper']


def score(directory, name):
    summary = json.loads((directory / 'compositor-refresh/summary.json').read_text())
    raw = json.loads((directory / 'compositor-refresh/sequence.json').read_text())
    stages = []
    for stage in STAGES:
        frames = [r for r in summary['recoveries'] if r['stage'] == stage]
        native = next((r for r in summary['stageReports'] if r['stage'] == stage), {})
        stages.append({'stage': stage, 'imagesSaved': len(frames),
                       'completeFramesObserved': native.get('completeFramesSinceBaseline', 0),
                       'ocrSamples': sum(r['ocrAvailable'] for r in frames),
                       'pageSamples': sum(any(r['markerRecovery'].values()) for r in frames),
                       'backdropSamples': sum(r['backdropLabelRecovered'] for r in frames)})
    return {'name': name, 'status': summary['status'], 'streamStopped': summary.get('streamStopped'),
            'targetPID': summary['targetPID'], 'targetBinarySHA256': summary['targetBinarySHA256'],
            'windowSharingEnabled': summary['windowSharingEnabled'], 'stages': stages,
            'error': raw.get('error'),
            'allStagesReadable': all(s['pageSamples'] > 0 for s in stages),
            'allStagesSampled': all(s['imagesSaved'] > 0 and s['ocrSamples'] == s['imagesSaved'] for s in stages)}


def run(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a new project artifact directory')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {'status': 'inconclusive', 'rows': [], 'systemInputPosted': False}
    try:
        manifest = json.loads((ROOT / 'docs/evidence/compositor-refresh-permission-manifest.json').read_text())
        if not manifest.get('permissionApproved'):
            raise RuntimeError('This helper has no recorded user consent')
        source = ROOT / 'Sources/Diagnostics/CompositorRefreshProbe.swift'
        if hashlib.sha256(source.read_bytes()).hexdigest() != manifest['sourceSHA256']:
            raise RuntimeError('The consent-pinned helper source changed')
        permission = invoke(['--permissions'], output / 'permissions.json')
        if not permission.get('screenRecordingGranted'):
            report['status'] = 'permission-required'
            return report
        frozen = json.loads((ROOT / 'docs/evidence/window-sharing-physical-results.json').read_text())['frozenImagesSHA256']
        for name, expected in frozen.items():
            binary = ROOT / 'dist' / (name + '.app') / 'Contents/MacOS' / name
            if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
                raise RuntimeError('An earlier granted image changed')
        for name in ['clear-before', 'restricted', 'clear-after']:
            directory = output / name
            trial(directory, 'compact', restricted=name == 'restricted',
                  use_physical_archive=True, compositor_refresh=True)
            row = score(directory, name)
            report['rows'].append(row)
            print(json.dumps(row), flush=True)
            if row['streamStopped'] is not True:
                raise RuntimeError('A stream failed before verified shutdown: ' + str(row['error']))
            if name.startswith('clear') and (row['error'] or row['status'] != 'sampled' or not row['allStagesReadable']):
                raise RuntimeError('A clear reference failed calibration')
        candidate = next(r for r in report['rows'] if r['name'] == 'restricted')
        if any(s['pageSamples'] for s in candidate['stages']):
            report['status'] = 'page-recovered'
        elif candidate['error'] or candidate['status'] != 'sampled' or not candidate['allStagesSampled']:
            report['status'] = 'inconclusive-no-candidate-samples'
        elif all(s['backdropSamples'] == s['imagesSaved'] for s in candidate['stages']):
            report['status'] = 'backdrop-only-in-sampled-frames'
        else:
            report['status'] = 'page-absent-in-sampled-frames'
        report['scope'] = 'Exact physical-test images. Three two-second stages, up to eight sampled frames each. Non-atomic coverage checks and queued frames remain limits.'
        return report
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        (output / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output)), flush=True)
