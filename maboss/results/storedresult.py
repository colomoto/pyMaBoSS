from .baseresult import BaseResult
import os

class StoredResult(BaseResult):

    def __init__(self, path, prefix="res"):
        
        self._path = path
        self._prefix = prefix
        BaseResult.__init__(self, self._path)
     
    def get_fp_file(self):
        return os.path.join(self._path, "%s_fp.csv" % self._prefix)

    def get_probtraj_file(self):
        return os.path.join(self._path, "%s_probtraj.csv" % self._prefix)

    def get_statdist_file(self):
        return os.path.join(self._path, "%s_statdist.csv" % self._prefix)
