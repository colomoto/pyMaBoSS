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
    version="0.8.17",
    packages=find_packages(exclude=["test"]),
    py_modules = ["maboss_setup", "maboss_setup_experimental"],
    author="Vincent Noël, Loic Paulevé, Aurelien Naldi and Nicolas Levy",
    author_email="vincent.noel@curie.fr",
    description="A python and jupyter API for the MaBoSS software",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url="https://maboss.curie.fr",
    install_requires = [
        "colomoto_jupyter >=0.4.10",
        "pyparsing",
        "ipywidgets",
        "matplotlib",
        "pandas",
        "scikit-learn",
        "networkx",
        "cmaboss>=1.0.0b34"
    ] + optional_contextlib,
    scripts=['scripts/MBSS_FormatTable.py', 'scripts/UpPMaBoSS.py']
)
