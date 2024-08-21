# tests/conftest.py
import sys
from pathlib import Path

# Add the project root directory to the Python path to enable importing testlib
sys.path.insert(0, Path(__file__).parent.as_posix())
