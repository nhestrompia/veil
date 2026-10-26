"""Read fixed staged readiness before the ordinary-user progress actor."""

import hashlib
import json
import os
import time

from observe_renderer_signals import private_stages, read_native
from run_renderer_progress_control import ACTOR, attack_renderer


def observe_progress(plan, baseline, output, launch_process):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError('The observer must use the ordinary account')
    if hashlib.sha256(ACTOR.read_bytes()).hexdigest() != plan['actorSHA256']:
        raise ValueError('The actor differs from the reviewed image')
    result = {'actorUID': os.getuid(), 'attempted': False,
              'supervisorHashScope': 'root-staging-verification-only',
              'appHashScope': 'ordinary-user-observer'}
    while launch_process.poll() is None:
        candidates = private_stages() - baseline
        if len(candidates) > 1:
            result['error'] = 'Multiple new research stages appeared. No signal attempt.'
            break
        if candidates:
            try:
                stage = next(iter(candidates))
                ready = read_native(stage, plan, progress_ready=True)
                if ready is not None:
                    result.update(attempted=True, stage=stage, ready=ready)
                    result['actor'] = attack_renderer(ready, output, isolated=True)
                    break
            except FileNotFoundError:
                pass
            except Exception as error:
                result['error'] = str(error)
                break
        time.sleep(0.01)
    (output / 'observer.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
