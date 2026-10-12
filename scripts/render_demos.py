#!/usr/bin/env python3
"""Generate shareable before/after reports from bundled synthetic data only."""
import argparse
import json
from pathlib import Path
from jira_import_doctor import diagnose, markdown

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path, help='New output directory')
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        parser.error('Output path already exists; choose a new directory')
    args.out.mkdir(parents=True, exist_ok=False)
    for case in ('cascade-hypothesis', 'platform-ambiguous'):
        sample = ROOT/'examples'/case
        csv = (sample/'input.csv').read_bytes()
        log = (sample/'import.log').read_bytes()
        context = json.loads((sample/'context.json').read_text())
        for stage, evidence in [('before-csv-only', b''), ('after-with-log', log)]:
            report = diagnose(csv, evidence, context)
            stem = f'{case}-{stage}'
            (args.out/(stem+'.json')).write_text(json.dumps(report, indent=2)+'\n')
            (args.out/(stem+'.md')).write_text('Synthetic demo: no Jira import was performed.\n\n'+markdown(report))
    print('Generated eight before/after reports from two synthetic examples')


if __name__ == '__main__':
    main()
