"""Tools for writing out ROOT canvases to different formats
"""
import ROOT
from string import Template
import subprocess
import os

standalone_template = Template(r'''
\documentclass[tikz]{standalone}
\begin{document}
\input{$filename}
\end{document}
''')

def fix_tex(tex_file, replace_dict):
    '''Open a tex file and replace keys with values from replace_dict
    '''
    with open(tex_file) as f:
        contents = f.read()
    for k, v in replace_dict.iteritems():
        contents = contents.replace(k, v)
    with open(tex_file, "w") as f:
        f.write(contents)

def make_standalone(tex_file, st_al_fname):
    '''Write a short latex document that makes a standalone pdf of one figure
    '''
    contents = standalone_template.substitute(filename = os.path.abspath(tex_file))
    with open(st_al_fname, "w") as f:
        f.write(contents)

def compile_standalone(tex_file):
    '''Run pdflatex to get the standalone
    '''
    return subprocess.check_call("pdflatex {0}".format(tex_file) , shell = True)


def clean_pdflatex_files(bs_name):
    '''Really don't need the extra pdflatex stuff to compile a picture once
    '''
    for ext in (".aux", ".log"):
        try:
            os.remove(bs_name + ext)
        except:
            pass


def save_as_tex_pdf(canvas, outname, replace_dict = None):
    '''Write a canvas to tex, create a standalone and compile it to PDF. Outname needs no extension
    '''
    if replace_dict is None:
        replace_dict = {}

    outname = os.path.splitext(os.path.abspath(outname))[0]
    tex_name = outname + "_input.tex"
    st_al_fname = outname + ".tex"

    canvas.SaveAs(tex_name)
    fix_tex(tex_name, replace_dict)
    make_standalone(tex_name, st_al_fname)
    compile_standalone(st_al_fname)
    clean_pdflatex_files(outname)
