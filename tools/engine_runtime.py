"""Launch only the isolated diagnostic with a verified research engine build."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from prepare_webkit_activity import ROOT, PATCH
from process_cleanup import matching_pids

BASE = ROOT / '.build/webkit-engine'
REQUIRED = {'WebKit', 'WebCore', 'JavaScriptCore'}


def engine_environment(root):
    root = root.resolve()
    if root != (BASE / 'output/Release').resolve():
        raise RuntimeError('Only the workspace research engine output is allowed')
    report = json.loads((BASE / 'build-results.json').read_text())
    receipt = json.loads((BASE / 'applied-source.json').read_text())
    if not report.get('engineCompiled') or report.get('exitCode') != 0:
        raise RuntimeError('The research engine build did not finish successfully')
    if receipt['patchSHA256'] != hashlib.sha256(PATCH.read_bytes()).hexdigest():
        raise RuntimeError('The research engine patch identity changed')
    for name in REQUIRED:
        if not (root / f'{name}.framework/{name}').is_file():
            raise RuntimeError(f'The research framework is missing: {name}')
    environment = {name: value for name, value in os.environ.items()
                   if not name.startswith(('DYLD_', '__XPC_DYLD_'))}
    for name in ['DYLD_FRAMEWORK_PATH', 'DYLD_LIBRARY_PATH',
                 '__XPC_DYLD_FRAMEWORK_PATH', '__XPC_DYLD_LIBRARY_PATH']:
        environment[name] = str(root)
    environment['WEBKIT_UNSET_DYLD_FRAMEWORK_PATH'] = 'YES'
    environment['AFB_RESEARCH_FRAMEWORK_ROOT'] = str(root)
    return environment


def launch_engine(log, arguments, root):
    binary = ROOT / 'dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl'
    existing = matching_pids(binary)
    if existing:
        raise RuntimeError('An internal diagnostic is already running')
    with log.open('w') as stream:
        process = subprocess.Popen([str(binary), *arguments], env=engine_environment(root),
                                   stdout=stream, stderr=subprocess.STDOUT)
    process.research_existing_pids = existing
    return process, binary


def mapped_frameworks(text, root):
    """Accept only exact framework binary paths below the expected build root."""
    root = root.resolve()
    found = {}
    for line in text.splitlines():
        # vmmap labels unused shared-cache fragments on a dirty page separately.
        if line.lstrip().startswith('unused '):
            continue
        match = re.search(r'(?<!\S)(/[^\n]*?/(WebKit|WebCore|JavaScriptCore)\.framework/(?:Versions/[^/]+/)?\2)(?:\s|$)', line)
        if not match:
            continue
        path = Path(match[1]).resolve()
        if not path.is_relative_to(root):
            raise RuntimeError(f'A system or unexpected framework is mapped: {match[2]} at {path}')
        found[match[2]] = str(path)
    if set(found) != REQUIRED:
        raise RuntimeError('Mapped framework identity is incomplete')
    return found


def verify_content(log, root, output):
    match = re.search(r'^ENGINE_DIAGNOSTIC contentPID=(\d+) contentExecutable=(.+)$', log.read_text(), re.M)
    if not match:
        raise RuntimeError('The diagnostic did not identify its content process')
    pid = int(match[1])
    executable = Path(match[2]).resolve()
    if not executable.is_relative_to(root.resolve()):
        raise RuntimeError('Content executable is outside the research engine')
    actual = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'comm='],
                            capture_output=True, text=True, check=True).stdout.strip()
    if Path(actual).resolve() != executable:
        raise RuntimeError('Content process executable identity changed')
    result = subprocess.run(['/usr/bin/vmmap', '-w', str(pid)],
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise RuntimeError('Content framework mapping is unavailable')
    framework_lines = [line for line in result.stdout.splitlines()
                       if any(f'/{name}.framework/' in line for name in REQUIRED)]
    output.with_suffix('.framework-lines.json').write_text(json.dumps(framework_lines, indent=2) + '\n')
    report = {'pid': pid, 'executable': str(executable),
              'mappedFrameworks': mapped_frameworks(result.stdout, root)}
    output.write_text(json.dumps(report, indent=2) + '\n')
    return report
