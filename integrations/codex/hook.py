"""Compatibility entrypoint. Prefer python -m devguard.client_hook after install."""
from devguard.client_hook import *  # noqa: F401,F403

if __name__ == '__main__':
    raise SystemExit(main())
