"""
namedtuple2
Enhancing Python namedtuples to allow for default arguments.
Source: http://blog.thomnichols.org/2010/12/lightweight-data-types-in-python
Renamed and slightly modified by David Baumgold <singingwolfboy@gmail.com>
"""
import sys
from copy import deepcopy
try:
    from collections import namedtuple
except ImportError:
    from collections_backport import namedtuple
    
def namedtuple2( name, *required, **defaults ):
    '''
    Similar to `collections.namedtuple` except default properties may be
    specified. For example:
    
    Person = namedtuple2('Person', 'name', 'address', age=10)
    bob = Person(name='bob', address='123 someplace')
    
    Note that all constructor parameters must be keyword args. Positional
    arguments are not supported at this time.
    '''
    # all properties is the union of required and defaulted properties
    all_props = required + tuple(defaults.keys())
    # We're starting off with a 'stock' namedtuple and modifying it slightly
    cls = namedtuple(name,all_props)
    
    # Here we are intercepting the normal __new__ call in order to assign 
    # defaults before all properties are passed to the namedtuple constructor. 
    # If there are any extra properties, they will be stripped before being
    # passed to old_new. If any properties are missing, the old_new will make 
    # that determination and throw the proper exception.
    old_new = cls.__new__
    def _new(cls, *args, **kwargs):
        # copy the defaults and update them
        new_args = deepcopy(defaults)
        new_args.update(kwargs)

        # The first item in our args list is the class itself.
        # Everything is are real positional arguments, which can be
        # associated with the positions in the _fields array.
        for i, val in enumerate(args[1:]):
            new_args[cls._fields[i]] = val
        
        # strip extra parameters
        for argtitle in kwargs:
            if argtitle not in cls._fields:
                del new_args[argtitle]
        
        return old_new(cls, **(new_args))
    cls.__new__ = _new.__get__(cls)
    # alternate method for assigning a new method
    # from types import MethodType 
    # cls.__new__ = MethodType(_new,cls)
    
    def _eq(self,other):
        '''Equality should depend on type as well as values'''
        return tuple.__eq__(self,other) and self.__class__ == other.__class__
    cls.__eq__ = _eq
    
    # TODO override __hash__ - two records of different 'type' that have the same
    # properties will have the same hash (I think). 
    
    # since this is wrapped, the proper module name is up another level:
    if hasattr(sys, '_getframe'):
        cls.__module__ = sys._getframe(1).f_globals.get('__name__', '__main__')
    
    return cls