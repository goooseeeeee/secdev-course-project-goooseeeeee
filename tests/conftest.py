import os

os.environ.setdefault("JWT_SECRET", "testsecret123")

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # корень репозитория
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
