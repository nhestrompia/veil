"""Read the fixed staged channel report before ordinary-user signal attempts."""

import hashlib
import json
import os
from pathlib import Path
import stat
import time

from observe_renderer_signals import STAGE_PATTERN, private_stages, read_fixed_file
from prepare_renderer_channel_run import APP_NAMES, HELPER, validate_url
from run_renderer_channel_preflight import actor, identity_arguments, one, records, USER_KEYS, GROUP_KEYS

LIMIT = 400 * 1024


def read_channel_stage(stage, plan, owner=0):
    stage = Path(stage)
    if not STAGE_PATTERN.fullmatch(str(stage)): raise ValueError('Unexpected stage')
    info = stage.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != owner: raise ValueError('Unexpected stage owner')
    if stat.S_IMODE(info.st_mode) == 0o700: return None
    if stat.S_IMODE(info.st_mode) != 0o711: raise ValueError('Unexpected stage permissions')
    raw = read_fixed_file(stage / 'observation.log', owner, 0o444, LIMIT)
    complete = raw.rsplit(b'\n', 1)[0] + b'\n' if b'\n' in raw else b''
    prefixes = ('CHANNEL_LAUNCHER_READY', 'CHANNEL_ATTACK_READY', 'CHANNEL_DISPLAY_READY')
    for prefix in prefixes:
        values = records(complete, prefix)
        if len(values) > 1: raise ValueError('Duplicate channel readiness')
        if not values: return None
    if not records(complete, 'CHANNEL_FRAME_PRESENTED'): return None
    for item in plan['manifest']:
        path = stage / item['staged']
        if item['staged'] == HELPER:
            info = path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner or info.st_nlink != 1
                    or stat.S_IMODE(info.st_mode) != 0o700 or info.st_size != item['size']):
                raise ValueError('Unexpected supervisor metadata')
            continue
        mode = 0o555 if '/MacOS/' in item['staged'] else 0o444
        data = read_fixed_file(path, owner, mode, item['size'])
        if len(data) != item['size'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Staged image differs from the reviewed manifest')
    launch, ready, display = [one(complete, prefix) for prefix in prefixes]
    _, nonce = validate_url(plan['fixtureURL'])
    if (launch['rootRun'] is not True or launch['permanentDropChecked'] is not True
            or launch['ordinaryUID'] != plan['ordinaryUID'] or launch['rendererUID'] != plan['isolatedUID']
            or launch['displayUID'] != plan['ordinaryUID'] or ready['sample']['nonce'] != nonce
            or ready['host']['pid'] != launch['rendererPID'] or display['host']['pid'] != launch['displayPID']):
        raise ValueError('Readiness does not match this cross-user comparison')
    if set(ready['services']) != {'content', 'gpu', 'network'}: raise ValueError('Incomplete role identities')
    for index, value in enumerate((ready['host'], display['host'])):
        expected = str(stage / (APP_NAMES[index] + '.app/Contents/MacOS/' + APP_NAMES[index]))
        if value['path'] != expected: raise ValueError('Readiness names another app')
    for value in (ready['host'], *ready['services'].values()):
        identity_arguments(value)
        if (not all(value.get(key) == plan['isolatedUID'] for key in USER_KEYS)
                or not all(value.get(key) == plan['isolatedGID'] for key in GROUP_KEYS)):
            raise ValueError('Wrong renderer credentials')
    identity_arguments(display['host'])
    if (not all(display['host'].get(key) == plan['ordinaryUID'] for key in USER_KEYS)
            or not all(display['host'].get(key) == plan['ordinaryGID'] for key in GROUP_KEYS)):
        raise ValueError('Wrong display credentials')
    return {'native': ready, 'display': display, 'launch': launch}


def observe(plan, baseline, directory, process):
    if os.getuid() != plan['ordinaryUID'] or os.geteuid() != os.getuid():
        raise ValueError('The observer must use the ordinary account')
    result = {'attempted': False, 'rootRun': False, 'supervisorHashScope': 'root-staging-verification-only'}
    while process.poll() is None:
        candidates = private_stages() - baseline
        if len(candidates) > 1:
            result['error'] = 'Multiple new stages. No signal attempt.'
            break
        if candidates:
            try:
                stage = next(iter(candidates))
                ready = read_channel_stage(stage, plan)
                if ready:
                    result.update(attempted=True, stage=stage, ready=ready)
                    attacks = {'renderer': actor(directory, ready['native'], None, isolated=True)}
                    attacks['display'] = actor(directory, ready['native'], ready['display'])
                    result['attacks'] = attacks
                    break
            except FileNotFoundError:
                pass
            except Exception as error:
                result['error'] = str(error)
                break
        time.sleep(0.01)
    (directory / 'observer.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
