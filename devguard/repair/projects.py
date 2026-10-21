"""Operator-reviewed startup manifests; no model or HTTP-selected execution scope."""
import json
from pathlib import Path
import re

from devguard.repair.contracts import ProjectSpec
from devguard.repair.workspace import read_source, safe_relative, MAX_TOTAL_BYTES


def canonical_directory(value):
    path = Path(value).expanduser().absolute()
    if path.is_symlink() or not path.is_dir() or path.resolve() != path:
        raise ValueError('Project/test directory must be canonical and not a symlink')
    return path


def load_projects(config_path):
    path = Path(config_path).absolute()
    if path.is_symlink() or path.stat().st_size > 32768:
        raise ValueError('Invalid project manifest')
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or set(data) != {'projects'} or not isinstance(data['projects'], list) or not 1 <= len(data['projects']) <= 8:
        raise ValueError('Manifest requires one to eight projects')
    specs, seen = [], set()
    for item in data['projects']:
        if set(item) != {'project_id', 'root', 'source_files', 'writable_files', 'trusted_tests', 'test_names', 'image_id'}:
            raise ValueError('Invalid project fields')
        identifier = item['project_id']
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', identifier) or identifier in seen:
            raise ValueError('Invalid or duplicate project ID')
        seen.add(identifier)
        root, checks = canonical_directory(item['root']), canonical_directory(item['trusted_tests'])
        source, writable, tests = item['source_files'], item['writable_files'], item['test_names']
        if not all(isinstance(v, list) and v and all(isinstance(n, str) for n in v) for v in (source, writable, tests)):
            raise ValueError('Explicit file and check lists are required')
        if len(source) > 32 or len(set(source)) != len(source) or not set(writable).issubset(source) or len(tests) > 8:
            raise ValueError('Invalid source scope')
        size = 0
        for name in source:
            safe_relative(name)
            size += len(read_source(root, name))
            # Independent tests cannot also be writable source.
            if (root / name).is_relative_to(checks):
                raise ValueError('Trusted tests must be separate from source')
        if size > MAX_TOTAL_BYTES:
            raise ValueError('Source scope exceeds the snapshot budget')
        for name in tests:
            if not re.fullmatch(r'[a-zA-Z0-9_]{1,80}', name):
                raise ValueError('Invalid named check')
            read_source(checks, 'test_' + name + '.py')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', item['image_id']):
            raise ValueError('An inspected Docker image ID is required')
        specs.append(ProjectSpec(identifier, root, tuple(source), tuple(writable), checks, tuple(tests), item['image_id']))
    return specs
