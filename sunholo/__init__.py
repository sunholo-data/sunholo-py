import os
import glob

# Get a list of all .py files in the package directory
module_files = glob.glob(os.path.dirname(__file__) + "/*.py")

# Exclude __init__.py itself
module_files = [f for f in module_files if not f.endswith('__init__.py')]

# Get the module names (remove the directory path and file extension)
modules = [os.path.basename(f)[:-3] for f in module_files]

# Import all modules dynamically
for module in modules:
    __import__(f"{__name__}.{module}", fromlist=[module])

# Set __all__ to include all imported modules
__all__ = modules