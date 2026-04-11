# Name: Samruddhi, stuti, sandhya
# Date: 04/10/2026
#Pytest configuration file. Adds the project root directory to the Python path so test modules can import app.py correctly.

import sys
import os

# Add the project root to the Python path so tests can import app.py
sys.path.insert(0, os.path.dirname(__file__))
