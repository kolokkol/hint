"""This module prodives a hint function to help new Pythoneers
with exception in their programs
"""

###############################################################################
###############################################################################
# Imports
###############################################################################

import glob
import io
import sys
import traceback
import os
import re 
import site

###############################################################################
###############################################################################
# Constants
###############################################################################

__author__ = 'Jesse Maarleveld'

###############################################################################
###############################################################################
# Create a list of all modules
###############################################################################

# Create an exhausive list of all modules and packages

# A considerable amount of time in this code is spent in looping
# and os.walk. To achieve better startup time, this should
# probably be rewritten in C.
modules = set()
p = os.path
for basepath in sys.path:
    for path, dirs, files in os.walk(basepath):
        for module in glob.glob(p.join(path, '*.py')):
            module = module[len(basepath)+1:].replace(p.sep, '.')
            modules.add(p.splitext(module)[0])
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

try:
    from _accelerate import ldist
except ImportError:
    try:
        from levenshtein import ldist
    except ImportError:
        pass
    else:
        differences = ldist
else:
    differences = ldist

def max_differences(word):
    """Determine the maximum allowed differences between two word.
    """
    return len(word) // 2 + len(word) // 4

def match(word, matches, extra=[]):
    likely = min(matches)
    matches[likely] = list(set(matches[likely] + extra))
    dif = max_differences(word)
    if likely > dif and not extra:
        return False
    elif likely > dif and extra:
        likely -= 1
        matches[likely] = extra
    elif likely > dif:
        return False
    return matches[likely]

def format_options(options):
    if len(options) == 1:
        return f'Did you mean {options[0]}?'
    return (f'Did you mean one of {", ".join(options[:-1])}'
            f' or {options[-1]}?')

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

    @classmethod
    def handle(cls, tp, inst, tb):
        module = inst.name
        matches = {}
        extra = []
        for mod in modules:
            matches.setdefault(differences(module, mod), []).append(mod)
            if set(mod) == set(module):
                extra.append(mod)
            # Too many possibilities with common stuff such as test
            #if mod in module or module in mod:
            #    extra.append(mod)
        mods = match(module, matches, extra)
        if not mods:
            return False
        return format_options(mods)
        

###############################################################################
###############################################################################
# AttributeError handler
###############################################################################


@register
class HandleAttributeError(AttributeError):

    # AttributeError error messages
    #
    # The following are the two most common ways an
    # error message for attribute errors is formed:
    #
    # type object 'name' has no attribute 'name'
    # 'name' object has not attribute 'name'
    #
    # depending on the error message either one
    # of the following must be True:
    #
    # type(obj).__name__ == 'type' and obj.__name__ == name
    # or
    # type(obj).__name__ == name

    pattern = re.compile(r'.*[\'"](.+)[\'"].*[\'"](.+)[\'"].*')
    is_type = re.compile(r'type object [\'"](.+)[\'"]')

    @classmethod
    def handle(cls, tp, inst, tb, *, strict=True):
        result = cls.pattern.search(inst.args[0])
        if result is None:
            return False
        obj, attr = result.groups()
        if not strict:
            attr = attr.replace('_', '')
        is_tp = cls.is_type.search(inst.args[0]) is not None
        current = tb
        while current.tb_next is not None:
            current = current.tb_next
        frame = current.tb_frame
        namespaces = (frame.f_locals, frame.f_globals, frame.f_builtins)
        if is_tp:
            for namespace in namespaces:
                for ob in namespace.values():
                    if issubclass(type(ob), type) and ob.__name__ == obj:
                        break
                else:
                    continue
                break
            else:
                return False
        else:
            for namespace in namespaces:
                for ob in namespace.values():
                    if type(ob).__name__ == obj:
                        break
                else:
                    continue
                break
            else:
                return False
        matches = {}
        extra = []
        for name in vars(ob):
            or_name = name
            if not strict:
                name = name.replace('_', '')
            matches.setdefault(differences(attr, name), []).append(or_name)
            if attr in name or name in attr:
                extra.append(or_name)
        attrs = match(attr, matches, extra)
        if not attrs and strict:
            return cls.handle(tp, inst, tb, strict=False)
        elif not attrs:
            return False
        return format_options(attrs)
    
            
###############################################################################
###############################################################################
# Handle exceptions related to undefined variables
###############################################################################

# issubclass(UnboundLocalError, NameError) == True

@register
class HandleUndefinedVariableError(NameError):

    pattern = re.compile(r'[\'"](.+)[\'"]')

    @classmethod
    def handle(cls, tp, inst, tb, *, strict=True):
        result = cls.pattern.search(inst.args[0])
        if result is None:
            return False
        attr, = result.groups()
        if not strict:
            attr = attr.replace('_', '')
        current = tb
        while current.tb_next is not None:
            current = current.tb_next 
        frame = current.tb_frame
        namespaces = (frame.f_locals, frame.f_globals, frame.f_builtins)
        matches = {}
        extra = []
        for namespace in namespaces:
            for name in namespace:
                or_name = name
                if not strict:
                    name = name.replace('_', '')
                matches.setdefault(differences(attr, name), []).append(or_name)
                if (name in attr or attr in name and
                        len(attr) + len(name) < len(attr) * 3):
                    extra.append(or_name)
        attrs = match(attr, matches, extra)
        if not attrs:
            if strict:
                return cls.handle(tb, inst, tb, strict=False)
            return False
        return format_options(attrs)


###############################################################################
###############################################################################
# Specialized errors during mathematical operations
###############################################################################


@register
class HandleZeroDivisionError(ZeroDivisionError):

    @classmethod
    def handle(cls, tp, inst, tb):
        return 'If you divide by 0 the universe will explode'


@register
class HandleOverflowError(OverflowError):

    @classmethod
    def handle(cls, tp, inst, tb):
        return 'Your calculation resulted in a result too large too handle'


@register
class HandleArithmeticError(ArithmeticError):

    @classmethod
    def handle(cls, tp, inst, tb):
        if tp in (ArithmeticError.__subclasses__()):
            return False
        
                
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
    result = io.StringIO()
    result.writelines('=================================================\n')
    result.write(f'{os.path.split(__file__)[1]} by {__author__}\n')
    result.write('-----------------------------------------------\n')
    if inst is None:
        result.write('No exception has occurred :)\n')
    else:
        for handler in _handlers:
            if issubclass(handler, tp):
                res = handler.handle(tp, inst, tb)
                if res:
                    break
        try:
            assert type(res) is str
            result.write(res + '\n')
        except AssertionError:
            result.write('Could not find any helpfull data.\n')
        except UnboundLocalError:
            # No matching exception was found;
            # No class had been implemented to handle
            # it yet
            result.write(f'Cannot help you with the following exception: {inst!r}\n')
    traceback.print_exception(tp, inst, tb)
    result.write('=================================================\n')
    result.seek(0)
    for line in result:
        print(line, file=sys.stderr, end='')


def test(st):
    exec(
    f"""
try:
    {st}
except:
    hint()
    """)
        
