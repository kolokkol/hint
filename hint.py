"""This module prodives a hint function to help new Pythoneers
with exception in their programs
"""

###############################################################################
###############################################################################
# Imports
###############################################################################
import glob
import sys
import os
import site

###############################################################################
###############################################################################
# Create a list of all modules
###############################################################################

# Create an exhausive list of all modules and packages
modules = set()
p = os.path
for basepath in sys.path:
    for path, dirs, files in os.walk(basepath):
        for module in glob.glob(p.join(path, '*.py')):
            module = p.splitext(module[len(basepath)+1:].replace(p.sep, '.'))[0]
            modules.add(module)
        for module in dirs:
            if p.exists(p.join(path, module, '__init__.py')):
                package = path[len(basepath):]
                modules.add(p.join(package, module).replace(p.sep, '.'))

###############################################################################
###############################################################################
# Utility functions
###############################################################################

def differences(a, b):
    """Calculate the amount of differences between two strings."""
    return abs(len(a) - len(b)) + sum(ca != cb for ca, cb in zip(a, b))

###############################################################################
###############################################################################
# Special registering function
###############################################################################

_handlers = []

def register(cls):
    """Register a handler for yse by the hint() function."""
    _handlers.append(cls)
    return cls

###############################################################################
###############################################################################
# ImportError handlers
###############################################################################
    

@register
class HandleModuleNotFoundError(ModuleNotFoundError):

    max_differences = 10

    @classmethod
    def handle(cls, tp, inst, tb):
        module = inst.name
        matches = {}
        for mod in modules:
            matches.setdefault(differences(module, mod), []).append(mod)
            if set(mod) == set(module):
                matches.setdefault(len(mod)-1, []).append(mod)
        likely = min(matches)
        if likely > cls.max_differences:
            return False
        mods = matches[likely]
        if len(mods) == 1:
            return f'Did you mean {mods[0]}?'
        return (f'Did you mean one of {", ".join(mods[:-1])}'
                f' or {mods[-1]}?')


###############################################################################
###############################################################################
# Actual hint function
###############################################################################


def hint(error=None):
    """Print a hit to help solve the given exception.
    If no exception is given, the exception which
    occurred last according to sys.exc_info() will be
    examined.
    """
    if error is None:
        tp, inst, tb = sys.exc_info()
    else:
        tp = type(error)
        inst = error
        tb = error.__traceback__
    if inst is None:
        print('No exception has happened :)')
        return
    for handler in _handlers:
        if issubclass(handler, tp):
            res = handler.handle(tp, inst, tb)
            if res:
                break
    print(res)


def test(st):
    exec(
    f"""
try:
    {st}
except:
    hint()
    """)
        
    

    
