from __future__ import print_function

from ..baseresult import BaseResult
import os
import tempfile
import subprocess
import sys
from random import random
import shutil


class EnsembleResult(BaseResult):

    def __init__(self, models_files, cfg_filename, prefix="res"):
        BaseResult.__init__(self)

        self.models_files = models_files
        self._cfg = cfg_filename
        self._path = tempfile.mkdtemp()
        self.prefix = prefix

        maboss_cmd = "MaBoSS"
        cmd_line = [maboss_cmd, "-c", self._cfg,'--ensemble',  "-o", self._path+'/'+self.prefix] + self.models_files
        
        res = subprocess.Popen(
            cmd_line,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        std_out, std_err = res.communicate()
        self._err = res.returncode
        if self._err != 0:
            print("Error, MaBoSS returned non 0 value", file=sys.stderr)
            print(std_err.decode())
        
        if len(std_out.decode()) > 0:
            print(std_out.decode())

    def get_fp_file(self):
        return os.path.join(self._path, "%s_fp.csv" % self.prefix)

    def get_probtraj_file(self):
        return os.path.join(self._path, "%s_probtraj.csv" % self.prefix)
        
    def get_statdist_file(self):
        return os.path.join(self._path, "%s_statdist.csv" % self.prefix)

    def __del__(self):
        shutil.rmtree(self._path)