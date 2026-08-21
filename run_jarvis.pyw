import sys
import os
import runpy

# Ensure the root directory is in sys.path and is the Current Working Directory
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# CRITICAL FIX: Windows Startup runs with CWD as System32. 
# We must change CWD to project root so .env and other relative paths load correctly!
os.chdir(root_dir)

if __name__ == '__main__':
    if '--background' not in sys.argv:
        sys.argv.append('--background')
    runpy.run_module('backend.main', run_name='__main__')
