from sys import version_info

from setuptools import setup, find_packages

optional_contextlib = []
if version_info[0] < 3:
    optional_contextlib.append("contextlib2")

setup(name='maboss',
    version="0.7.4",
    packages=find_packages(exclude=["test"]),
    py_modules = ["maboss_setup"],
    author="Nicolas Levy",
    author_email="nicolaspierrelevy@gmail.com",
    description="A python and jupyter API for the MaBoSS software",
    install_requires = [
        "colomoto_jupyter >=0.4.10",
        "pyparsing",
        "ipywidgets",
        "matplotlib",
        "pandas",
    ] + optional_contextlib)
