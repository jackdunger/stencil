from setuptools import setup
from glob import glob
setup(name = "stencil",
      version = "1.0.0",
      description = "Plot Tools for PP theses",
      author = "Jack Dunger",
      packages = ["stencil"],
      scripts = glob("bin/*")
)
