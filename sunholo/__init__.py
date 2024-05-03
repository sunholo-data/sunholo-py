import os
import importlib.util

def import_submodules(package_name):
    """Import all submodules of a package."""
    package_path = os.path.dirname(__file__)
    package_dir = os.path.join(package_path, package_name)
    imported_modules = []
    
    # Traverse the directory structure
    for root, dirs, files in os.walk(package_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('_'):
                module_name = os.path.splitext(file)[0]
                module_path = os.path.relpath(os.path.join(root, file), package_path)
                module_name = package_name + '.' + module_path.replace(os.path.sep, '.')
                
                # Import the module dynamically
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(package_path, module_path))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                imported_modules.append(module_name)
    
    return imported_modules

# Import submodules dynamically and get the list of imported modules
imported_modules = import_submodules('sunholo')

# Set __all__ to include all imported modules
__all__ = imported_modules
