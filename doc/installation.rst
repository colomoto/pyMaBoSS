Installation
============

pyMaBoSS can be installed either via Conda, PyPi or GitHub. 


Installation with Conda
-----------------------

This is the recommended option, as it also allows the simple installation of all the dependencies. 

   conda -c colomoto install pymaboss
   
This will install the library, which will already be ready to use. 


Installation with PyPi
----------------------

This is not the recommended option as it cannot yet package the MaBoSS binaries, but if you already have then install you can just install pyMaBoSS using

   pip install maboss
   

To download the MaBoSS binaries, if you have conda and if you are using linux or macosx, you can run : 

   python -m maboss-setup
   
Otherwise, you can download them using the following links, for `Linux <https://github.com/sysbio-curie/MaBoSS-env-2.0/releases/latest/download/MaBoSS-linux64.zip>`_, `MacOSX <https://github.com/sysbio-curie/MaBoSS-env-2.0/releases/latest/download/MaBoSS-osx64.zip>`_ or `Windows <https://github.com/sysbio-curie/MaBoSS-env-2.0/releases/latest/download/MaBoSS-win64.zip>`_. Once downloaded, you need to make them accessible by putting them in a folder configured in your PATH. 

Installation with GitHub
------------------------

Finally, you can also install pyMaBoSS directly from the official GitHub repository : 

   git clone https://github.com/colomoto/pyMaBoSS
   
   cd pyMaBoSS
   
   python setup.py install
   
Note that this also comes without the MaBoSS binaries, so to install them you'll have to follow the steps described above. 
