#!/usr/bin/env python3
"""Copy-and-run checks in isolated host-shaped folders, not a host-discovery test."""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from validate_skill import validate

ROOT = pathlib.Path(__file__).resolve().parents[1]
OFFLINE_GUARD = """
import runpy, sys

def guard(event, args):
    if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system'}:
        raise RuntimeError('Network/process operation blocked by offline smoke guard: ' + event)

sys.addaudithook(guard)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix='jira-doctor-install-') as tmp:
        for host, path in [('claude-code', '.claude/skills'), ('codex', '.agents/skills')]:
            project = pathlib.Path(tmp) / host
            target = project / path / 'jira-import-doctor'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            validation = validate(target)
            sample = target/'examples/cascade-hypothesis'
            command = [sys.executable, '-I', '-c', OFFLINE_GUARD, str(target/'scripts/jira_import_doctor.py'), '--csv', str(sample/'input.csv'), '--log', str(sample/'import.log'), '--context', str(sample/'context.json'), '--out', str(project/'report')]
            run = subprocess.run(command, cwd=project, capture_output=True, text=True)
            assert run.returncode == 0, run.stderr
            report = json.loads((project/'report/report.json').read_text())
            assert report['csv']['record_count'] == 4
            assert sum(f['code'] == 'POSSIBLE_PARENT_CASCADE' for f in report['findings']) == 2
            results.append({'host_layout': host, 'copy_and_cli': 'passed', 'outside_source_cwd': True, 'socket_and_subprocess_guard': 'passed', 'package_validation': validation, 'host_discovery': 'not_tested'})
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
