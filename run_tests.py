# run_tests.py
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Run pytest
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main())