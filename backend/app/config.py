"""
Config — Environment Variable Loading

Loads .env files exactly once, at import time, so local development works
without manually exporting environment variables in every shell.

Precedence (highest wins):
1. Real environment variables (Render, Docker, CI)
2. .env at the project root
3. .env inside backend/

`load_dotenv(..., override=False)` never overwrites an existing variable,
so production configuration always takes precedence over local files.

Import this module before any code that reads os.getenv() at import time
(database.py, services/auth.py, alembic/env.py).
"""

from pathlib import Path

from dotenv import load_dotenv

# backend/app/config.py -> backend/app -> backend -> project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = Path(__file__).resolve().parents[1]

for _env_file in (_PROJECT_ROOT / ".env", _BACKEND_ROOT / ".env"):
    if _env_file.exists():
        load_dotenv(_env_file, override=False)
