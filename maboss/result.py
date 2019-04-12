"""
Class that contains the results of a MaBoSS simulation.
"""

from __future__ import print_function

from .baseresult import BaseResult

from sys import stderr, stdout, version_info
if version_info[0] < 3:
    from contextlib2 import ExitStack
else:
    from contextlib import ExitStack
import shutil
import tempfile
import os
import subprocess


class Result(BaseResult):

    def __init__(self, simul, command=None, workdir=None, overwrite=False):
        BaseResult.__init__(self, simul, command)

        self.workdir = workdir
        if workdir is None:
            self._path = tempfile.mkdtemp()
        else:
            self._path = workdir
            if os.path.exists(self._path) and overwrite:
                shutil.rmtree(self._path)
                os.mkdir(self._path)
            
            elif not os.path.exists(self._path):
                os.mkdir(self._path)

        if workdir is None or overwrite:

            cfg_fd, self._cfg = tempfile.mkstemp(dir=self._path, suffix='.cfg')
            os.close(cfg_fd)
            
            bnd_fd, self._bnd = tempfile.mkstemp(dir=self._path, suffix='.bnd')
            os.close(bnd_fd)
            
            with ExitStack() as stack:
                bnd_file = stack.enter_context(open(self._bnd, 'w'))
                cfg_file = stack.enter_context(open(self._cfg, 'w'))
                simul.print_bnd(out=bnd_file)
                simul.print_cfg(out=cfg_file)

            maboss_cmd = simul.get_maboss_cmd()
            if command:
                maboss_cmd = command

            self._err = subprocess.call([maboss_cmd, "-c", self._cfg, "-o",
                                        self._path+'/res', self._bnd])
            if self._err:
                print("Error, MaBoSS returned non 0 value", file=stderr)

    def get_fp_file(self):
        return "{}/res_fp.csv".format(self._path)

    def get_probtraj_file(self):
        return "{}/res_probtraj.csv".format(self._path)
    
    def get_statdist_file(self):
        return "{}/res_statdist.csv".format(self._path)
    
    def save(self, prefix, replace=False):
        """
        Write the cfg, bnd and all results in working dir.

        prefix is a string that will determine the name of the created files.
        If there is a conflict with existing files, the existing files will be
        replaced or not, depending on the value of the replace argument.
        """
        if not _check_prefix(prefix):
            return

        # Create the results directory
        try:
            os.makedirs(prefix)
        except OSError:
            if not replace:
                print('Error directory already exists: %s' % prefix,
                      file=stderr)
                return
            elif prefix.startswith('rpl_'):
                shutil.rmtree(prefix)
                os.makedirs(prefix)
            else:
                print('Error only directries begining with "rpl_" can be'
                      'replaced', file=stderr)
                return

        # Moves all the files into it
        shutil.copy(self._bnd, prefix+'/%s.bnd' % os.path.basename(prefix))
        shutil.copy(self._cfg, prefix+'/%s.cfg' % os.path.basename(prefix))

        maboss_files = filter(lambda x: x.startswith('res'),
                              os.listdir(self._path))
        for f in maboss_files:
            shutil.copy(self._path + '/' + f, prefix)

    def __del__(self):
        if self.workdir is None:
            shutil.rmtree(self._path)



class StoredResult(BaseResult):

    def __init__(self, path, prefix="res"):
        
        self._path = path
        self._prefix = prefix
        BaseResult.__init__(self)
     
    def get_fp_file(self):
        return os.path.join(self._path, "%s_fp.csv" % self._prefix)

    def get_probtraj_file(self):
        return os.path.join(self._path, "%s_probtraj.csv" % self._prefix)

    def get_statdist_file(self):
        return os.path.join(self._path, "%s_statdist.csv" % self._prefix)

def _check_prefix(prefix):
    if type(prefix) is not str:
        print('Error save method expected string')
        return False
    return True

__all__ = ["Result", "StoredResult"]
