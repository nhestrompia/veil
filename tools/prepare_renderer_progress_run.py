"""Prepare one hash-bound cross-user progress comparison without elevation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

from prepare_renderer_identity_run import ROOT, prepare, stage_script
from run_renderer_progress_control import ACTOR


def prepare_progress_plan(output):
    plan = prepare(output, progress=True)
    script = stage_script(plan['manifest'], os.getuid(), plan['libraries'], observe_signals=True, progress=True)
    command = '/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C /bin/sh -c ' + shlex.quote(script)
    subprocess.run(['codesign', '--verify', '--strict', str(ACTOR)], check=True, capture_output=True)
    plan.update(administratorCommand=command,
        administratorCommandSHA256=hashlib.sha256(command.encode()).hexdigest(),
        actorSHA256=hashlib.sha256(ACTOR.read_bytes()).hexdigest(), actorUID=os.getuid(),
        runCount=1, maximumRuns=1, repeatOnFailure=False, stopAfterFirstFailure=True,
        attemptConsumedAt='Administrator-command invocation, including staging failure',
        progressSampleDelaySeconds=3, fixture='Fixed inline page, no network requests or external URL',
        scope='One fixed nobody renderer progress comparison. Ordinary user signals exact host/content/GPU/network records. Root only stages, supervises its own dropped child and watchdog, and removes fixed staging files. Root never acts on reported service PIDs.',
        observation={'file': 'observation.log', 'ownerUID': 0, 'mode': '0444',
                     'maximumReadBytes': 3 * 1024 * 1024 + 16384,
                     'purpose': 'Publish fixed readiness before the ordinary actor and final progress report.'},
        requiredResults=['Helper exits zero', 'Baseline rendering and nobody credentials pass',
            'All four pause attempts denied', 'Fresh challenge starts strictly after actor completion',
            'Timer, DOM challenge, yellow redraw, and final identities pass',
            'Measured processes exit and staging disappears'])
    plan['ordinarySourceSHA256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'Sources/Diagnostics/HeadlessRendererProbe.swift', 'Sources/Diagnostics/RendererIdentitySupervisor.c',
        'Sources/Diagnostics/RendererSignalActor.c', 'scripts/build-renderer-progress-control.sh',
        'scripts/build-renderer-progress-supervisor.sh', 'tools/prepare_renderer_identity_run.py',
        'tools/prepare_renderer_progress_run.py', 'tools/run_renderer_progress_control.py',
        'tools/test_renderer_progress_control.py', 'tools/test_renderer_progress_stage.py', 'tools/observe_renderer_signals.py',
        'tools/run_renderer_signal_reference.py', 'tools/observe_renderer_progress.py',
        'tools/run_renderer_progress_comparison.py')}
    plan['uncertainties'].extend(['One inline page and one sampled redraw do not prove general website compatibility.',
        'No post-attack network request or worker progress is measured.',
        'A late actor makes the sample ordering inconclusive.',
        'Metadata and signals are separate non-atomic diagnostic operations.'])
    output.write_text(json.dumps(plan, indent=2) + '\n')
    return plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    plan = prepare_progress_plan(parser.parse_args().output)
    print(json.dumps({'rootRun': False, 'administratorCommandSHA256': plan['administratorCommandSHA256'],
                      'maximumRuns': 1, 'actorSHA256': plan['actorSHA256']}))
