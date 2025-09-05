# This file allows the backend directory to be imported as a Python package
# and ensures proper import paths are available

import os
import sys

# Add the parent directory to sys.path if it's not already there
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)