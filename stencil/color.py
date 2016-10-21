'''Color schemes are just dictionaries matching names to ROOT colors. 
   fetch one by name using get_color_scheme
'''
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import sys

default = {
    "uchain"     : ROOT.TColor.GetColor("#4b6ebc"),
    "thchain"    : ROOT.TColor.GetColor("#669966"),
    "cosmogenic" : ROOT.TColor.GetColor("#00cccc"),
    "b8"         : ROOT.TColor.GetColor("#996633"),
    "external"   : ROOT.TColor.GetColor("#ff9900"),
    "twonu"      : 15
}


'''Return a basic list of colors for ROOT plots. Default to these when no
   color specified by name
'''
backup_list =  [ROOT.kRed, ROOT.kBlue, ROOT.kViolet, ROOT.kOrange, 
               ROOT.kBlue, ROOT.kBlack, ROOT.kMagenta]


def get_color_scheme(name):
    '''Find a color scheme in this module by name
    '''
    return getattr(sys.modules[__name__], name)
