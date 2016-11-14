''' Tools for putting ROOT objects onto canvas
'''
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
import stencil.rio as rio
import stencil.color as color

def get_obj_with_attr(obj_list, attr_name):
    '''Get a ref to obj with attribute <attr_name> 
    '''
    return filter(lambda x: hasattr(x, attr_name), obj_list)

def get_attribute_refs(obj_list, attr_name):
    '''Get a ref to the attribute <attr_name> for each object that has one
    ''' 
    return [getattr(x, attr_name) for x in get_obj_with_attr(obj_list, attr_name)]


def get_method_results(obj_list, method_name):
    '''For every object in list, get ref to method result if it exists else skip
    '''
    attrs = get_attribute_refs(obj_list, method_name)
    return [x.__call__() for x in attrs if callable(x)]

def apply_color_scheme(obj_dict, color_scheme):
    '''Look for a color associated with colorable objects name, or fall back to 
       a backup set
    '''
    backup_list = color.backup_list
    backup_count = 0
    for nm, obj in obj_dict.iteritems():
        try:
            obj.SetLineColor(color_scheme[nm])        
        except KeyError: 
            # no color for this name
            obj.SetLineColor(backup_list[backup_count % len(backup_list)])
            backup_count += 1
        except AttributeError:
            # doesnt have a line..
            pass
            
            
def apply_fill(obj_dict):
    '''Take every object with a line color and make that the fill color too
    '''
    for fl, ln in zip((get_attribute_refs(obj_dict.values(), "SetFillColor")), get_method_results(obj_dict.values(), "GetLineColor")):
        fl(ln)

def normalise(obj_dict):
    '''Normalise everything we can
    '''
    for sm, ing in zip((get_attribute_refs(obj_dict.values(), "Scale")), get_method_results(obj_dict.values(), "Integral")):
        sm(1./ing)

def apply_line_style(obj_dict, line_style):
    '''Optionally override the existing line styles
    '''
    for ref in get_attribute_refs(obj_dict.values(), "SetLineStyle"):
        ref(line_style)
                

class PlotOverlay(object):
    '''Class for overlaying root objects onto canvas with an (optional) legend
    '''
    def __init__(self, no_legend = False, canvas = None, 
                 auto_scale_x = True, auto_scale_y = True, auto_scale_max = True,
                 color_scheme = "", leg_pos = (0.7, 0.7, 0.9, 0.9), log_x = False, 
                 log_y = False, add_fill = False, x_title = "xaxis", y_title = "yaxis",
                 title = "title", x_title_offset = 1., y_title_offset = 1., 
                 x_title_size = 0.04, y_title_size = 0.04, line_style = -1,
                 normalise = False
                 ):
        '''Initilise with draw options. By default the legend is drawn, axes are scaled
        to display all hists and the legend is drawn in the top right corner
        '''
        self.obs              = {}
        self.draw_opts        = {}
        self.legend           = ROOT.TLegend(*leg_pos)
        self.no_legend        = no_legend
        self.canvas           = canvas
        self.auto_scale_x     = auto_scale_x
        self.auto_scale_y     = auto_scale_y
        self.auto_scale_max   = auto_scale_max
        self.x_title          = x_title
        self.y_title          = y_title
        self.title            = title
        self.log_y            = log_y
        self.log_x            = log_x
        self.add_fill         = add_fill
        self.x_title_offset   = x_title_offset
        self.y_title_offset   = y_title_offset
        self.normalise        = normalise
        self.x_title_size   = x_title_size
        self.y_title_size   = y_title_size
        if line_style == -1:
            self.line_style = None
        else:
            self.line_style = line_style

        if color_scheme != "":
            self.color_scheme = color.get_color_scheme(color_scheme)
        else:
            self.color_scheme = None

        if self.canvas is None:
            self.canvas = ROOT.TCanvas()        

    def add_obj(self, obj, name, draw_opt = "", leg_opt = "L", leg_name = None):
        '''Add an object to the overlay. leg_name can optionally differ from key name
        '''
        if leg_name is None:
            leg_name = name
        self.obs[name] = obj
        self.legend.AddEntry(obj, leg_name, leg_opt)
        self.draw_opts[name] = draw_opt

    def add_stack(self, stack, name):
        '''Add a hist stack object. It has its own colors, and several entries for the legend
        '''
        stack.build()
        self.obs[name] = stack.thstack
        self.draw_opts[name] = ""
        # now add all the internal histograms to the legend
        for n, h, o in zip(stack.leg_names.values(), stack.hists.values(), stack.leg_options.values()):
            self.legend.AddEntry(h, n, o)

    def set_titles(self):
        '''Set the title for everything with a title
        '''
        for x in get_attribute_refs(self.obs.values(), "SetTitle"):
            x(self.title)

    def set_x_titles(self):
        '''Set the x title for everything with x axis
        '''
        for x in get_method_results(self.obs.values(), "GetXaxis"):
            x.SetTitle(self.x_title)
            x.SetTitleOffset(self.x_title_offset)
            x.SetTitleSize(self.x_title_size)

    def set_y_titles(self):
        '''Set the y title for everything with x axis
        '''
        for y in get_method_results(self.obs.values(), "GetYaxis"):
            y.SetTitle(self.y_title)
            y.SetTitleOffset(self.y_title_offset)
            y.SetTitleSize(self.y_title_size)

    def set_x_range(self, low, high):
        '''Set the x-axis range of all relevant objects at once
        '''
        for x in get_method_results(self.obs.values(), "GetXaxis"):
            x.SetRangeUser(low, high)

    def set_y_range(self, low, high):
        '''Set the y-axis range of all relevant objects at once,
           don't do this if we are already setting to maximum
        '''
        if not self.auto_range_maxima:
            for x in get_method_results(self.obs.values(), "GetYaxis"):
                x.SetRangeUser(low, high)

    def set_maxima(self, set_max):
        '''Set the maximum on any object with that option
        '''
        for x in get_attribute_refs(self.obs.values(), "SetMaximum"):
            x(set_max)

    def auto_range_x(self):
        '''Adjust everything with an xaxis to have the same scale
        '''
        # work out the furthest extents of any of the x-axes
        overall_max = None
        overall_min = None

        for xaxis in get_method_results(self.obs.values(), "GetXaxis"):
            this_min = xaxis.GetBinLowEdge(xaxis.GetFirst())
            this_max = xaxis.GetBinUpEdge(xaxis.GetLast())

            if overall_max is None:
                overall_max = this_max
                overall_min = this_min
            else:
                overall_max = max(overall_max, this_max)
                overall_min = min(overall_min, this_min)
        
        if overall_max is not None:
            self.set_x_range(overall_min, overall_max)

    def auto_range_y(self):
        '''Adjust everything with an yaxis to have the same scale
        '''
        # work out the furthest extents of any of the y-axes
        overall_max = None
        overall_min = None
        for obj in self.obs.values():
            for yaxis in get_method_results(self.obs.values(), "GetYaxis"):
                this_min = yaxis.GetBinLowEdge(yaxis.GetFirst())
                this_max = yaxis.GetBinUpEdge(yaxis.GetLast())

                if overall_max is None:
                    overall_max = this_max
                    overall_min = this_min
                else:
                    overall_max = max(overall_max, this_max)
                    overall_min = min(overall_min, this_min)

        if overall_max is not None:
            self.set_y_range(overall_min, overall_max)

    def auto_range_maxima(self):
        '''Adjust everything to have the same maxima
        '''
        maxes = get_method_results(self.obs.values(), "GetMaximum")
        if maxes != []:
            self.set_maxima(max(maxes))

    def draw(self):
        '''Draw the objects on a copy of the canvas, 
           and return it to caller
        '''
        self.canvas.Clear()
        self.canvas.cd()

        # ROOT seg faults if you dont draw them without "SAME first", so one of these is 
        # drawn twice...
        for k, v in self.obs.iteritems():
            v.Draw(self.draw_opts[k])

        for k, v in self.obs.iteritems():
            v.Draw("SAME" + self.draw_opts[k])


        if self.auto_scale_x:
            self.auto_range_x()
        if self.auto_scale_y:
            self.auto_range_y()
        if self.auto_scale_max:
            self.auto_range_maxima()

        self.set_x_titles()
        self.set_y_titles()
        self.set_titles()
        if not self.no_legend:
            self.legend.Draw("same")    

        if self.color_scheme is not None:
            apply_color_scheme(self.obs, self.color_scheme)

        if self.add_fill is True:
            apply_fill(self.obs)
            
        if self.line_style is not None:
            apply_line_style(self.obs, self.line_style)

        if self.log_x is True:
            self.canvas.SetLogx()
        if self.log_y is True:            
            self.canvas.SetLogy()                    
            
        if self.normalise is True:
            normalise(self.obs)
        self.canvas.Update()
        return self.canvas



class HistStack(object):
    '''Class for overlaying histograms into THStacks
    '''
    def __init__(self, options_dict):
        '''Initialise everything. Save references to hists themselves, 
           so we can add them to a 
           legend somewhere else. Saved in dicts so easy to 
           add color/style by name later. Options_dict is the contr arguments to 
           PlotOverlay. You need a subset of them at this stage
        '''

        self.color_scheme = None
        if options_dict["color_scheme"] != "":
            self.color_scheme = color.get_color_scheme(options_dict["color_scheme"])
        else:
            self.color_scheme = None
        self.line_style = None
        if options_dict["line_style"]:
            self.line_style = options_dict["line_style"]

        self.thstack   =  ROOT.THStack()
        self.hists     = {}
        self.leg_names = {}
        self.leg_options = {}

    def add_hist(self, hist, name, leg_name = None, leg_option = "F"):
        '''Add a histogram to the stack (not assembled yet). Optional different 
           name in legend to key
        '''
        if leg_name is None:
            leg_name = name

        self.hists[name] = hist
        self.leg_names[name] = leg_name
        self.leg_options[name] = leg_option

    def build(self):
        '''Piece it together
        '''
        self.thstack = ROOT.THStack()
        if self.color_scheme is not None:
            apply_color_scheme(self.hists, self.color_scheme)
            apply_fill(self.hists)

        if self.line_style is not None:
            apply_line_style(self.hists, self.line_style)

        for i, hist in enumerate(self.hists.values()):
            self.thstack.Add(hist)
        return self.thstack
