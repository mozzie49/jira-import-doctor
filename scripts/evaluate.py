#!/usr/bin/env python3
"""Deterministic log ablation on bundled synthetic examples; no LLM benchmark."""
import argparse
import json
from pathlib import Path
from jira_import_doctor import diagnose

ROOT = Path(__file__).resolve().parents[1]


def compact(report):
    return {'records': report['csv']['record_count'], 'definite_file_defects': sorted({f['code'] for f in report['findings'] if f['category'] == 'file_defect'}), 'codes': sorted({f['code'] for f in report['findings']}), 'correlation': report['correlation_coverage'], 'counts': report['reconciliation']['status'], 'reported_counts': report['reconciliation'].get('reported_counts', {}), 'destination_verified': report['reconciliation']['destination_verified']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public-csv', type=Path)
    parser.add_argument('--public-log', type=Path)
    args = parser.parse_args()
    if bool(args.public_csv) != bool(args.public_log):
        parser.error('Supply both public fixture paths')
    results = []
    for case in ['graph-errors', 'cascade-hypothesis', 'platform-ambiguous']:
        folder = ROOT/'examples'/case
        csv = (folder/'input.csv').read_bytes()
        log = (folder/'import.log').read_bytes()
        context = json.loads((folder/'context.json').read_text())
        baseline, full = compact(diagnose(csv, b'', context)), compact(diagnose(csv, log, context))
        results.append({'case': case, 'provenance': 'synthetic', 'csv_only': baseline, 'csv_plus_log': full, 'additional_finding_codes': sorted(set(full['codes']) - set(baseline['codes']))})
    output = {'method': 'Same deterministic engine with log withheld versus included; not an agent or competing product comparison', 'cases': results}
    if args.public_csv:
        context = json.loads((ROOT/'examples/platform-ambiguous/context.json').read_text())
        output['public_attachment_check'] = compact(diagnose(args.public_csv.read_bytes(), args.public_log.read_bytes(), context))
        output['public_attachment_check']['provenance'] = 'User-specified external file paths; attribution must be verified separately'
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
