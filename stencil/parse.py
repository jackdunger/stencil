''' A parser that knows the arguments needed to construct a given class by 
    name. At the moment assumes they all have defaults. To upgrate just drop 
    the leading args. If for some bizarre reason you tried it with built ins, 
    it won't work - unless you're on pypy. Then it might
''' 

import inspect
from argparse import ArgumentParser

def read_args(function):
    '''Returns a list of argument names for a function, their 
       defaults and types. Ignore self for method calls
    '''
    args_spec = inspect.getargspec(function)
    names = [x for x in args_spec[0] if x != "self"]
    defaults = args_spec[3]
    types = [type(x) for x in args_spec[3]]
    return names, defaults, types

class ConstructorParser(object):
    """Just an argparse with a bunch of built in params that are returned
       as a separate dictionary
    """
    def __init__(self, cls):
        '''Set up the built in arguments
        '''
        self.parser = ArgumentParser()
        self.construct_args = []
        self.cls = cls
        self.add_defaults()
        
    def add_argument(self, *args, **kwargs):
        '''Just pass this on to the parser inside
        '''
        self.parser.add_argument(*args, **kwargs)


    def add_defaults(self):
        '''Automatically add the arguments of our classes constructor 
           to this parser
        '''
        for arg, deft, typ in zip(*read_args(self.cls.__init__)):
            if typ == bool:
                self.add_argument("--{0}".format(arg), action = "store_true")
            else:
                self.add_argument("--{0}".format(arg), default = deft, type = typ)
            self.construct_args.append(arg)
            
    def parse_args(self):
        '''Do the normal parse, but split some off 
        to make our cls object and return two dicts
        '''
        raw_parse = vars(self.parser.parse_args())
        for_constr   = {}
        other_parts  = {}
        for k, v in raw_parse.iteritems():
            if k in self.construct_args:
                for_constr[k] = v
            else:
                other_parts[k] = v

        return for_constr, other_parts
