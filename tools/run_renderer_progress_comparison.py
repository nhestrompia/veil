"""Run one separately approved, committed cross-user progress comparison."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from observe_renderer_progress import observe_progress
from observe_renderer_signals import LIMIT, STAGE_PATTERN, private_stages
from prepare_renderer_identity_run import ROOT
from run_renderer_progress_control import ACTOR, identities, verify_progress
from run_renderer_signal_reference import prefixed

PLAN = ROOT / 'docs/evidence/renderer-progress-reviewed-run-plan.json'
REVIEWED_COMMAND_SHA256 = 'c972281b573e05269d6edce68f92e9aed980c3f3b0d845f07684d06516b83b1c'


def verify_inputs(plan):
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if plan['maximumRuns'] != 1 or plan['repeatOnFailure'] is not False:
        raise ValueError('Expected one reviewed invocation without retry')
    if (plan['administratorCommandSHA256'] != REVIEWED_COMMAND_SHA256
            or hashlib.sha256(plan['administratorCommand'].encode()).hexdigest() != REVIEWED_COMMAND_SHA256):
        raise ValueError('The reviewed command differs from its hash')
    for item in plan['manifest']:
        if Path(item['source']).stat().st_size != item['size'] or sha(item['source']) != item['sha256']:
            raise ValueError('A staged image differs from the reviewed manifest')
    for name, expected in plan['ordinarySourceSHA256'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('An ordinary source differs from the reviewed plan')
    if sha(ACTOR) != plan['actorSHA256']:
        raise ValueError('The ordinary actor differs from its reviewed image')


def run(directory):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError('The controller must use the ordinary account')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a new workspace artifact directory')
    plan = json.loads(PLAN.read_text())
    verify_inputs(plan)
    directory.mkdir()
    result = {'passed': False, 'attemptsConsumed': 1, 'maximumApprovedRuns': 1,
              'ordinaryUIDBefore': os.getuid(), 'administratorCommandSHA256': plan['administratorCommandSHA256']}
    (directory / 'request.json').write_text(json.dumps(result, indent=2) + '\n')
    command = plan['administratorCommand']
    apple_literal = json.dumps(command, ensure_ascii=False)
    baseline = private_stages()
    with (directory / 'administrator.stdout').open('wb') as output, (directory / 'administrator.stderr').open('wb') as errors:
        process = subprocess.Popen(['/usr/bin/osascript', '-e', 'do shell script ' + apple_literal + ' with administrator privileges'],
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=errors)
        try:
            observer = observe_progress(plan, baseline, directory, process)
        except Exception as error:
            observer = {'attempted': False, 'error': str(error)}
        finally:
            # Root's own-child deadlines and fixed cleanup own its lifecycle. Never kill reported PIDs here.
            process.wait()
        result['administratorExitCode'] = process.returncode
    try:
        path = directory / 'administrator.stdout'
        if path.stat().st_size > LIMIT:
            raise ValueError('The administrator report exceeds its byte limit')
        stdout = path.read_bytes()
        records = {}
        for name, prefix in (('ready', 'RENDERER_PROGRESS_READY '), ('native', 'HEADLESS_RENDERER_RESULT '),
                             ('supervisorReady', 'SUPERVISOR_READY '), ('supervisor', 'SUPERVISOR_RESULT '),
                             ('staging', 'STAGING_RESULT ')):
            values = prefixed(stdout, prefix)
            if len(values) != 1:
                raise ValueError('Expected one complete ' + name + ' report')
            records[name] = values[0]
        native = records['native']
        png = base64.b64decode(native.pop('snapshotPNGBase64'), validate=True)
        if len(png) > 2 * 1024 * 1024 or not png.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Invalid final image')
        (directory / 'snapshot.png').write_bytes(png)
        if observer.get('attempted') is not True or observer.get('ready') != records['ready']:
            raise ValueError('The observer lacks the exact published readiness record')
        verification = verify_progress(records['ready'], native, observer['actor'], isolated=True)
        record_ids = identities(records['ready'])
        credential_names = ('realUID', 'effectiveUID', 'savedUID', 'realGID', 'effectiveGID', 'savedGID')
        credentials = all(all(value[key] == 4294967294 for key in credential_names) for value in record_ids.values())
        known = {value['pid'] for value in record_ids.values()} | {records['supervisorReady']['watchdogPID']}
        deadline = time.monotonic() + 5
        while True:
            live = {int(value) for value in subprocess.run(['/bin/ps', '-axo', 'pid='],
                    capture_output=True, text=True, check=True).stdout.split()}
            remaining = sorted(known & live)
            if not remaining or time.monotonic() >= deadline:
                break
            time.sleep(0.05)
        stage = records['staging']['temporaryDirectory']
        staging_removed = bool(STAGE_PATTERN.fullmatch(stage)) and not Path(stage).exists()
        supervisor = records['supervisor']
        result.update(records=records, observer=observer, verification=verification,
                      credentialsPassed=credentials, remainingMeasuredPIDs=remaining,
                      stagingRemoved=staging_removed, snapshotSHA256=hashlib.sha256(png).hexdigest())
        result['passed'] = (process.returncode == 0 and records['staging']['helperExitCode'] == 0
            and records['staging']['stagingRemoved'] is True and staging_removed
            and supervisor['passed'] is True and supervisor['cleanupVerified'] is True
            and supervisor['hostReaped'] is True and supervisor['watchdogReaped'] is True
            and records['supervisorReady']['permanentDropChecked'] is True
            and credentials and verification['passed'] and not remaining)
        verify_inputs(plan)
    except Exception as error:
        result['passed'] = False
        result['error'] = str(error)
    result['ordinaryUIDAfter'] = os.getuid()
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--execute-reviewed-comparison', action='store_true', required=True)
    result = run(parser.parse_args().out)
    print(json.dumps({'passed': result['passed'], 'attemptsConsumed': 1, 'ordinaryUIDAfter': os.getuid()}))
    raise SystemExit(0 if result['passed'] else 1)
