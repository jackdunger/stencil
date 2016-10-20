''' A parser that knows the arguments needed to construct a given class by 
    name. If for some bizarre reason you tried it with built ins, 
    it won't work - unless you're on pypy. Then it might
''' 
from argparse import ArgumentParser
import inspect
import os
import hashlib

def read_args(function):
    '''Returns a list of kwargument names for a function, their 
       defaults and types
    '''
    args_spec = inspect.getargspec(function)
    names = [x for x in args_spec[0] if x != "self"]
    defaults = args_spec[3]
    types = [type(x) for x in args_spec[3]]

    # trim away the ordinary args (including possibly self)
    names = names[len(names) - len(defaults):]
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
            elif typ in (tuple, list):              
                self.add_argument("--{0}".format(arg), type = type(deft[0]), default = deft, nargs = len(deft))
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

def is_latex(st):
    '''Is this a math mode latex str?
    '''
    return type(st) == str and ("$" in st)

def unique_id(st):
    '''Make the identifiers close to unique. We dont want e.g. 
       x_title and title confused. Hash gives names much longer than 
       the eventual strings so text comes out tiny. Truncate here to 
       correct length (at small risk of collisions)
    '''
    return str(hashlib.md5(st).hexdigest())[:min(len(st), 5)]

def make_replace_dict(config, replace_dict):
    '''To use the tex output we need to hide math mode from ROOT
       easiest way to do this is to inject all labels after the tex build.
       So loop over the config dictionary, taking note of all strings and 
       replacing them with unique identifiers. Note, config is edited in 
       place
    '''
    for k, v in config.iteritems():
        if is_latex(v):
            uid = unique_id(v)
            replace_dict[uid] = v
            config[k] = uid

        if type(v) == list and any(is_latex(x) for x in v):
            names = v
            uids = [unique_id(x) for x in v]
            config[k] = uids
            for nm, uid in zip(names, uids):
                replace_dict[uid] = nm
    return config, replace_dict
            
def making_pdf(extension):
    '''Are we building a PDF?
    '''
    return extension == ".pdf"

def prepare_for_ext(cf1, cf2, extension):
    '''Do extension specific manipulation for the plot parameters
    '''
    replace_dict = {}
    if making_pdf(extension):
        cf1, replace_dict = make_replace_dict(cf1, replace_dict)
        cf2, replace_dict = make_replace_dict(cf2, replace_dict)        
    return cf1, cf2, replace_dict
