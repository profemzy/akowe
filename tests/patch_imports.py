"""Patch imports for testing."""

import os
import sys
import importlib
import importlib.abc
import importlib.machinery
from types import ModuleType
from typing import Optional

# Get the root path of the project
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class PatchedModuleFinder(importlib.abc.MetaPathFinder):
    """Custom meta path finder to patch imports for testing."""

    def find_spec(self, fullname, path, target=None):
        """Find the module spec, handling akowe.* imports specially."""
        # Handle akowe.models, akowe.app and other submodules
        akowe_modules = (
            'akowe.models', 'akowe.app', 'akowe.api', 'akowe.utils',
            'akowe.models.', 'akowe.app.', 'akowe.api.', 'akowe.utils.'
        )
        is_akowe_module = fullname in akowe_modules
        if not is_akowe_module:
            is_akowe_module = any(fullname.startswith(prefix) for prefix in akowe_modules)

        if is_akowe_module:
            # Extract the subpath from akowe.module[.x]
            if '.' in fullname:
                module_name, rest = fullname.split('.', 1)
                if '.' in rest:
                    main_module, submodules = rest.split('.', 1)
                    subpath = main_module + '.' + submodules
                else:
                    subpath = rest
            else:
                subpath = fullname
            
            # Handle submodules within models
            submodule_parts = subpath.split('.')
            filepath = os.path.join(PROJECT_ROOT, 'akowe', *submodule_parts)
            
            if os.path.isdir(filepath):
                filepath = os.path.join(filepath, '__init__.py')
            else:
                filepath += '.py'
            
            if os.path.exists(filepath):
                loader = importlib.machinery.SourceFileLoader(fullname, filepath)
                is_pkg = os.path.isdir(filepath[:-12] if filepath.endswith('__init__.py') else filepath[:-3])
                return importlib.machinery.ModuleSpec(fullname, loader, is_package=is_pkg)
        
        # Handle other akowe.* imports
        elif fullname.startswith('akowe.'):
            # Extract the subpath from akowe.[x]
            subpath = fullname[len('akowe.'):]
            
            # Split into path parts
            path_parts = subpath.split('.')
            filepath = os.path.join(PROJECT_ROOT, 'akowe', *path_parts)
            
            if os.path.isdir(filepath):
                filepath = os.path.join(filepath, '__init__.py')
            else:
                filepath += '.py'
            
            if os.path.exists(filepath):
                loader = importlib.machinery.SourceFileLoader(fullname, filepath)
                is_pkg = os.path.isdir(filepath[:-12] if filepath.endswith('__init__.py') else filepath[:-3])
                return importlib.machinery.ModuleSpec(fullname, loader, is_package=is_pkg)
        
        return None


def patch_imports():
    """Install the patched module finder at the beginning of sys.meta_path."""
    sys.meta_path.insert(0, PatchedModuleFinder())