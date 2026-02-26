"""
Secretary - Personal AI assistant for calendar and task management.

This package initialization ensures that the root directory is in the Python path
so that config.py can be imported from anywhere within the src package.
"""

import sys
from pathlib import Path

# Add project root to Python path for config imports
_root_dir = Path(__file__).parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))
