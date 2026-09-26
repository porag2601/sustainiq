"""Shared pytest setup. pytest loads this file automatically before any test.

app.main loads Settings at import time, and Settings requires an API key and
model name. Tests must not depend on a developer's real .env (or leak a real
key), so dummy values are set here before any test imports app.main.
setdefault keeps a value that is already set, e.g. in CI.
"""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("CLAUDE_MODEL", "test-model")
