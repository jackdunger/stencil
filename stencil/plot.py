''' Tools for putting ROOT objects onto canvas
'''
import ROOT
import stencil.rio as rio

def default_colors():
    '''Return a basic list of colors for ROOT plots
    '''
    return [ROOT.kRed, ROOT.kBlue, ROOT.kViolet, ROOT.kOrange, 
            ROOT.kBlue, ROOT.kBlack, ROOT.kMagenta]

def get_attribute_refs(obj_list, attr_name):
    '''Get a ref to the attribute <attr_name> for each object that has one
    ''' 
    attrs = []
    for x in obj_list:
        try:
            attrs.append(getattr(x, attr_name)) 
        except AttributeError as e:
            continue
    return attrs


def get_method_results(obj_list, method_name):
    '''For every object in list, get ref to method result if it exists else skip
    '''
    attrs = get_attribute_refs(obj_list, method_name)
    return [x.__call__() for x in attrs if callable(x)]

class PlotOverlay(object):
    '''Class for overlaying root objects onto canvas with an (optional) legend
    '''
    def __init__(self, no_legend = False, canvas = None, 
                 auto_scale_x = True, auto_scale_y = True, auto_scale_max = True,
                 colors = None, leg_pos = (0.7, 0.7, 0.9, 0.9), log_x = False, 
                 log_y = False, add_fill = False, x_title = "xaxis", y_title = "yxais", title = "title"
                 ):
        '''Initilise with draw options. By default the legend is drawn, axes are scaled
        to display all hists and the legend is drawn in the top right corner
        '''
        self.obs              = {}
        self.draw_opts        = {}
        self.colors           = colors 
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
        if self.canvas is None:
            self.canvas = ROOT.TCanvas()        

    def add_obj(self, obj, name, draw_opt = "", leg_opt = "L", leg_name = None):
        '''Add an object to the overlay. leg_name can optionally differ from key name
        '''
        if leg_name is None:
            leg_name = name
        self.obs[name] = obj
        self.legend.AddEntry(obj, name, leg_opt)
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

    def set_titles(self, title):
        '''Set the title for everything with a title
        '''
        for x in get_attribute_refs(self.obs.values(), "SetTitle"):
            x(title)

    def set_x_titles(self, title):
        '''Set the x title for everything with x axis
        '''
        for x in get_method_results(self.obs.values(), "GetXaxis"):
            x.SetTitle(title)

    def set_y_titles(self, title):
        '''Set the y title for everything with x axis
        '''
        for y in get_method_results(self.obs.values(), "GetYaxis"):
            y.SetTitle(title)

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

        if self.colors is not None:
            for i, mtd in enumerate(get_attribute_refs(self.obs.values(), "SetLineColor")):
                mtd(self.colors[i%len(self.colors)])
                

        if self.add_fill is True:
            for fl, ln in zip((get_attribute_refs(self.obs.values(), "SetFillColor")), get_method_results(self.obs.values(), "GetLineColor")):
                fl(ln)

        self.set_x_titles(self.x_title)
        self.set_y_titles(self.y_title)        
        self.set_titles(self.title)
        if not self.no_legend:
            self.legend.Draw("same")    

        if self.log_x is True:
            self.canvas.SetLogx()
        if self.log_y is True:            
            self.canvas.SetLogy()                    

        self.canvas.Update()
        return self.canvas



class HistStack(object):
    '''Class for overlaying histograms into THStacks
    '''
    def __init__(self, colors = None):
        '''Initialise everything. Save references to hists themselves, 
           so we can add them to a 
           legend somewhere else. Saved in dicts so easy to add color/style by name later
        '''
        self.colors = colors

        if self.colors is None:
            self.colors = default_colors()
        
        self.thstack   =  ROOT.THStack()
        self.hists     = {}
        self.leg_names = {}
        self.leg_options = {}

    def add_hist(self, hist, name, leg_option = "", leg_name = None):
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
        for i, hist in enumerate(self.hists.values()):
            hist.SetLineColor(self.colors[i%len(self.colors)])
            hist.SetFillColor(self.colors[i%len(self.colors)])
            self.thstack.Add(hist)
        return self.thstack


def plot_single_obj(filename, key_name = None, options_dict = None, 
                    draw_opt = ""):
    '''Make a canvas with a single histogram from disk, defaults to first 
       key if no arg given
    '''
    if options_dict is None:
        options_dict = {}
    obj = rio.grab_obj(filename, key_name)
    overlay = PlotOverlay(**options_dict)
    overlay.add_obj(obj, "h", draw_opt)
    return overlay.draw()


