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

def zip_files(filename1, filename2):
    '''Zip together the objects in file1 and file2 into list of pairs
    '''
    obs1 = grab_all_obs(filename1)
    obs2 = grab_all_obs(filename2)
    common_len = min(len(obs1), len(obs2))
    return [(obs1[i], obs2[i]) for i in xrange(common_len)]

def get_common_obs(filename1, filename2):
    '''Zip together all the objects in file1 with objects of matching name in filename 2
    '''    
    shared_keys = get_keys(filename1)
    shared_keys = [x for x in shared_keys if has_key(filename2, x)]
    return [(grab_obj(filename1, x), grab_obj(filename2, x)) for x in shared_keys]
