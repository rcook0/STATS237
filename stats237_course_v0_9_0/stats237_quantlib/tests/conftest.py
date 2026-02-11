import sys
from pathlib import Path

# Ensure the package (../stats237_quantlib) is importable when running tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
