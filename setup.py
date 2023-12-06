from sys import version_info

from setuptools import setup, find_packages

optional_contextlib = []
if version_info[0] < 3:
    optional_contextlib.append("contextlib2")

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "description.rst").read_text()

setup(name='maboss',
    version="0.8.6",
    packages=find_packages(exclude=["test"]),
    py_modules = ["maboss_setup"],
    author="Vincent Noël, Loic Paulevé, Aurelien Naldi and Nicolas Levy",
    author_email="vincent.noel@curie.fr",
    description="A python and jupyter API for the MaBoSS software",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    install_requires = [
        "colomoto_jupyter >=0.4.10",
        "pyparsing",
        "ipywidgets",
        "matplotlib",
        "pandas",
        "scikit-learn",
        "cmaboss>=1.0.0b19"
    ] + optional_contextlib,
    scripts=['scripts/MBSS_FormatTable.py', 'scripts/UpPMaBoSS.py']
)
