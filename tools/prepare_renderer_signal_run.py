"""Prepare one unexecuted cross-user signal experiment with fixed staging."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

from prepare_renderer_identity_run import ROOT, prepare, stage_script
from run_renderer_signal_reference import ACTOR


def prepare_signal_plan(output):
    plan = prepare(output)
    script = stage_script(plan['manifest'], os.getuid(), plan['libraries'], observe_signals=True)
    command = '/usr/bin/env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin LC_ALL=C /bin/sh -c ' + shlex.quote(script)
    subprocess.run(['codesign', '--verify', '--strict', str(ACTOR)], check=True, capture_output=True)
    plan.update({'administratorCommand': command,
                 'administratorCommandSHA256': hashlib.sha256(command.encode()).hexdigest(),
                 'actorSHA256': hashlib.sha256(ACTOR.read_bytes()).hexdigest(),
                 'actorUID': os.getuid(), 'runCount': 1, 'rootRun': False,
                 'scope': 'One fixed inline renderer launch as nobody. The ordinary-user actor attempts SIGSTOP and SIGCONT against its exact host/content/GPU/network records. Root never acts on reported service PIDs.',
                 'observation': {'file': 'observation.log', 'ownerUID': 0, 'mode': '0444',
                                 'maximumReadBytes': 3 * 1024 * 1024 + 16384,
                                 'purpose': 'Publish only the fixed research fixture report during its two-second hold.'},
                 'repeatOnFailure': False})
    plan['ordinarySourceSHA256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'Sources/Diagnostics/RendererSignalActor.c', 'scripts/build-renderer-signal-actor.sh',
        'tools/prepare_renderer_identity_run.py', 'tools/prepare_renderer_signal_run.py',
        'tools/run_renderer_signal_reference.py', 'tools/observe_renderer_signals.py')}
    plan['uncertainties'].append('The fixture report precedes signals. Post-attack website progress is not measured.')
    output.write_text(json.dumps(plan, indent=2) + '\n')
    return plan


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan = prepare_signal_plan(args.output)
    print(json.dumps({'rootRun': False, 'administratorCommandSHA256': plan['administratorCommandSHA256'],
                      'actorSHA256': plan['actorSHA256']}))
