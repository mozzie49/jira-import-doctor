#!/usr/bin/env python3
"""Minimal package validation, not agent discovery or a complete security audit."""
import argparse
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_IMPORTS = {'__future__', 'argparse', 'csv', 'hashlib', 'html', 'io', 'json', 're', 'sys', 'collections', 'pathlib'}


def validate(root):
    skill = (root/'SKILL.md').read_text(encoding='utf-8')
    if not skill.startswith('---\n') or '\n---\n' not in skill[4:]:
        raise ValueError('SKILL.md needs YAML frontmatter')
    head = skill[4:].split('\n---\n', 1)[0]
    metadata = {}
    for line in head.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if ':' not in line:
            raise ValueError('Minimal validator supports one-line scalar frontmatter fields only')
        key, value = line.split(':', 1)
        metadata[key.strip()] = value.strip()
    for key in ('name', 'description'):
        if not metadata.get(key):
            raise ValueError(f'Missing required frontmatter value: {key}')
    if metadata['name'] != root.name or not re.fullmatch('[a-z0-9-]{1,64}', metadata['name']):
        raise ValueError('Skill name must match its lower-case directory name')
    for resource in ('scripts/jira_import_doctor.py', 'references/contract.md', 'references/sources.md'):
        if not (root/resource).is_file():
            raise ValueError(f'Missing required relative resource: {resource}')
    checked_links = 0
    for document in root.rglob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'):
                continue
            if not (document.parent/link.split('#')[0]).is_file():
                raise ValueError(f'Broken relative link in {document.name}: {link}')
            checked_links += 1
    tree = ast.parse((root/'scripts/jira_import_doctor.py').read_text(encoding='utf-8'))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(item.name.split('.')[0] for item in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module.split('.')[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'exec', 'eval', '__import__'}:
            raise ValueError('Runtime contains dynamic code/import execution; review required')
    if imports - RUNTIME_IMPORTS:
        raise ValueError('Unexpected runtime imports; review required: ' + ', '.join(sorted(imports - RUNTIME_IMPORTS)))
    return {'required_frontmatter': 'passed', 'relative_links_checked': checked_links, 'declared_runtime_imports': sorted(imports), 'runtime_import_allowlist': 'passed', 'live_host_discovery': 'not_tested', 'security_audit': 'not_claimed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.skill_dir.resolve()), indent=2))
    except (OSError, ValueError, SyntaxError) as error:
        parser.exit(2, f'Validation failed: {error}\n')


if __name__ == '__main__':
    main()
