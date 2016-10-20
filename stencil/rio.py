'''Functions for manipulating ROOT files with a filename only interface
'''

import ROOT
import re

def get_keys(filename):
    '''Get all the object names in filename
    '''
    rt_f = ROOT.TFile(filename)
    return [x.GetName() for x in rt_f.GetListOfKeys()]

def has_key(filename, key_name):
    '''Is there a key with name key_name in filename1?
    '''
    return key_name in get_keys(filename)

def all_have_key(filenames, key_name):
    '''Is there a key named key_name in every file in the list
    '''
    return all(has_key(x, key_name) for x in filenames)

def is_histogram(obj):
    '''Is this object a ROOT histogram? Test the class name against regex
    '''
    cls_name = obj.__class__.__name__
    return re.match("^TH[0-3][CSIFD]$", cls_name) is not None

def grab_obj(filename, obj_name = None):
    '''Grab an object by name, or the first object in a ROOT file
    '''
    f  = ROOT.TFile(filename)
    if obj_name is not None:
        ob = f.Get(obj_name)
    else:
        ob = f.Get(f.GetListOfKeys()[0].GetName())
    if is_histogram(ob):
        ob.SetDirectory(0)
    return ob


def grab_all_obs(filename):
    '''Grab all the objects inside root file as python list
    '''
    f = ROOT.TFile(filename)
    obs = [f.Get(key) for key in get_keys(filename)]
    for ob in obs:
        if is_histogram(ob):
            ob.SetDirectory(0)
    return obs

def contains_only_hists(filename):
    '''Does the file contain only histograms?
    '''
    return all([is_histogram(x) for x in grab_all_obs(filename)])

def zip_files(filenames):
    '''Zip together the objects in filenames into list of lists
    '''
    obs_list = [grab_all_obs(x) for x in filenames]
    common_len = min(obs_list)
    return [[x[i] for x in obs_list ] for i in xrange(common_len)]

def get_common_obs(filenames):
    '''Zip together all the objects in filename list with same name
    '''    
    shared_keys = get_keys(filenames[0])
    shared_keys = [x for x in shared_keys if all_have_key(filenames, x)]
    return [[grab_obj(fn, kn) for fn in filenames] for kn in shared_keys]
