"""Execute one separately approved, pinned cross-user channel comparison."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from observe_renderer_channel import observe
from observe_renderer_signals import private_stages, STAGE_PATTERN
from prepare_renderer_channel_run import ROOT, validate_url
from run_renderer_channel_control import fixture
from run_renderer_channel_preflight import verify, one

PLAN = ROOT / 'docs/evidence/renderer-channel-reviewed-run-plan.json'
CONSUMED = ROOT / 'artifacts/renderer-channel-115-authorization-consumed.json'
REVIEWED_COMMAND_SHA256 = 'cf036154143bcef942203c0cf890c034f4f5cebb38f98439cbaec0fd359c6494'
REVIEWED_PLAN_SHA256 = '9dbe42e583dc813b63f6ea04c46fdf98b31c94bb5ae5549c11edeaedf34e563c'


def verify_inputs(plan):
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if hashlib.sha256((json.dumps(plan, indent=2) + '\n').encode()).hexdigest() != REVIEWED_PLAN_SHA256:
        raise ValueError('The comparison plan differs from the reviewed bytes')
    if (plan['maximumRuns'] != 1 or plan['repeatOnFailure'] is not False
            or plan['ordinaryUID'] != os.getuid() or plan['ordinaryGID'] != os.getgid()):
        raise ValueError('Expected one reviewed invocation for this account')
    if (plan['administratorCommandSHA256'] != REVIEWED_COMMAND_SHA256
            or hashlib.sha256(plan['administratorCommand'].encode()).hexdigest() != REVIEWED_COMMAND_SHA256):
        raise ValueError('The administrator command differs from the reviewed hash')
    for item in plan['manifest']:
        if Path(item['source']).stat().st_size != item['size'] or sha(item['source']) != item['sha256']:
            raise ValueError('A staged image changed')
    for name, expected in {**plan['sourceSHA256'], **plan['actorSHA256']}.items():
        if sha(ROOT / name) != expected: raise ValueError('A reviewed ordinary input changed')
    validate_url(plan['fixtureURL'])


def run(directory):
    if os.getuid() != 501 or os.geteuid() != os.getuid(): raise ValueError('Use the ordinary research account')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'): raise ValueError('Use a new workspace artifact directory')
    plan = json.loads(PLAN.read_text())
    verify_inputs(plan)
    if CONSUMED.exists(): raise ValueError('The one-run allowance is already consumed')
    port, nonce = validate_url(plan['fixtureURL'])
    directory.mkdir()
    result = {'passed': False, 'attemptsConsumed': 0, 'ordinaryUIDBefore': os.getuid(),
        'administratorCommandSHA256': REVIEWED_COMMAND_SHA256}
    (directory / 'request.json').write_text(json.dumps(result, indent=2) + '\n')
    with fixture(port=port, nonce=nonce) as (url, _, receipts):
        if url != plan['fixtureURL']: raise ValueError('Unexpected fixture binding')
        baseline = private_stages()
        with CONSUMED.open('x') as consumed:
            json.dump({'administratorCommandSHA256': REVIEWED_COMMAND_SHA256, 'output': str(directory),
                       'reason': 'One invocation consumed before requesting administrator authentication'}, consumed)
        result['attemptsConsumed'] = 1
        with (directory / 'administrator.stdout').open('wb') as output, (directory / 'administrator.stderr').open('wb') as errors:
            literal = json.dumps(plan['administratorCommand'], ensure_ascii=False)
            process = subprocess.Popen(['/usr/bin/osascript', '-e', 'do shell script ' + literal + ' with administrator privileges'],
                stdin=subprocess.DEVNULL, stdout=output, stderr=errors)
            try:
                observer = observe(plan, baseline, directory, process)
            except Exception as error:
                observer = {'attempted': False, 'error': str(error)}
            finally:
                # Root's finite own-child lifecycle owns cleanup. Do not signal reported PIDs here.
                process.wait()
            result['administratorExitCode'] = process.returncode
        try:
            path = directory / 'administrator.stdout'
            if path.stat().st_size > 420 * 1024: raise ValueError('Oversized administrator report')
            raw = path.read_bytes()
            staging = one(raw, 'STAGING_RESULT')
            if observer.get('attempted') is not True or 'attacks' not in observer:
                raise ValueError('The ordinary observer did not complete both attacks')
            if observer['ready']['native'] != one(raw, 'CHANNEL_ATTACK_READY'):
                raise ValueError('The observer used another readiness report')
            verification = verify(raw, observer['attacks'], nonce, receipts, isolated=True)
            known = verification['measuredPIDs']
            deadline = time.monotonic() + 6
            while True:
                live = {int(value) for value in subprocess.run(['/bin/ps', '-axo', 'pid='],
                        capture_output=True, text=True, check=True).stdout.split()}
                remaining = sorted(set(known) & live)
                if not remaining or time.monotonic() >= deadline: break
                time.sleep(0.05)
            stage = staging['temporaryDirectory']
            removed = bool(STAGE_PATTERN.fullmatch(stage)) and not Path(stage).exists() and stage == observer['stage']
            result.update(observer=observer, verification=verification, staging=staging,
                remainingMeasuredPIDs=remaining, stagingRemoved=removed, fixtureReceipts=receipts)
            result['passed'] = (process.returncode == 0 and staging['helperExitCode'] == 0
                and staging['stagingRemoved'] and removed and verification['passed'] and not remaining)
            verify_inputs(plan)
        except Exception as error:
            result['error'] = str(error)
    result['ordinaryUIDAfter'] = os.getuid()
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--execute-reviewed-comparison', action='store_true', required=True)
    result = run(parser.parse_args().out)
    print(json.dumps({'passed': result['passed'], 'attemptsConsumed': result['attemptsConsumed'],
                     'ordinaryUIDAfter': result['ordinaryUIDAfter']}))
    raise SystemExit(0 if result['passed'] else 1)
