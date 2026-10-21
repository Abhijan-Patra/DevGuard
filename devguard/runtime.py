"""Trusted local workspace selection; never write to installed package files."""
import os
from pathlib import Path


def workspace_root():
    configured = os.environ.get('DEVGUARD_HOME')
    if configured:
        path = Path(configured).expanduser().absolute()
        if path.resolve() != path:
            raise ValueError('DEVGUARD_HOME must be a canonical directory, without symlinks')
        return path
    source = Path(__file__).resolve().parents[1]
    if (source / 'pyproject.toml').is_file() and (source / 'scripts/devguard-local').is_file():
        return source
    return Path.home().resolve() / '.devguard-workspace'


def runtime_directory():
    return workspace_root() / '.devguard'
