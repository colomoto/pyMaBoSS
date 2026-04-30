from .network import *
from .simulation import *
from .result import *
from .results import *
from .gsparser import load, loadBNet, loadSBML, loadTabularQual
from .server import MaBoSSClient
from .upp import UpdatePopulation
from .ensemble import EnsembleResult, Ensemble
from .pop import PopSimulation
import platform 
import maboss.pipelines
from . import temporal_logic
from .temporal_logic import MaBoSSEvaluator

from colomoto_jupyter import IN_IPYTHON
import colomoto.setup_helper

if IN_IPYTHON:
    from colomoto_jupyter import jupyter_setup
    from .widgets import *

    import matplotlib.pyplot as plt
    plt.ion()

    jupyter_setup("mymodule",
        label="MaBoSS",
        color="green", # for menu and toolbar
        menu=menu,
        toolbar=toolbar,
        js_api=js_api)


if platform.system() == "Windows":
    bin_name = "MaBoSS.exe"
else:
    bin_name = "MaBoSS"
if shutil.which(bin_name) is None:

    if platform.system() == "Windows":
        bin_path = os.path.join(os.getenv("APPDATA"), "maboss", "bin")
    else:
        bin_path = os.path.join(os.path.expanduser("~"), ".local", "share", "maboss", "bin")

    if os.path.exists(bin_path):
        if platform.system() == "Windows":
            os.environ["PATH"] = "%s;%s" % (bin_path, os.environ["PATH"])
        else:
            os.environ["PATH"] = "%s:%s" % (bin_path, os.environ["PATH"])
