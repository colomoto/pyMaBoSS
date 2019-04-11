from __future__ import print_function

from ..baseresult import BaseResult
from ..simulation import _default_parameter_list
from ..gsparser import load
import os
import tempfile
import subprocess
import sys
from random import random
import shutil


class EnsembleResult(BaseResult):

    def __init__(self, path, cfg_filename=None, *args, **kwargs):
        BaseResult.__init__(self)

        self.models_path = path
        self.param = _default_parameter_list
        self.nodes = []
        self.models_files = [os.path.join(self.models_path, file) for file in os.listdir(self.models_path)]
        self.read_nodes(self.models_files[0])

        self._path = tempfile.mkdtemp()
        if cfg_filename is None:
            self._cfg = os.path.join(self._path, "model.cfg")

            self.istates = {}
            self.outputs = []
            self.mutations = {}
            for p in kwargs:
                if p in self.param:
                    self.param[p] = kwargs[p]
                elif p == "istate":
                    self.istates = kwargs[p]
                elif p == "outputs":
                    self.outputs = kwargs[p]
                elif p == "mutations":
                    self.mutations = kwargs[p]

            # self.param['seed_pseudorandom'] = random()*1000
            self.write_cfg()
            self.write_mutations()

        else:
            self._cfg = cfg_filename
        
        maboss_cmd = "MaBoSS"
        cmd_line = [maboss_cmd, "-c", self._cfg,'--ensemble',  "-o", self._path+'/res'] + self.models_files
        
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

    def read_nodes(self, filename):

        if os.path.splitext(filename)[1] == ".bnet":
            self.read_bnet_nodes(filename)
        elif os.path.splitext(filename)[1] == ".bnd":
            self.read_maboss_nodes(filename)
        else:
            print("Unknown model type")

    def read_maboss_nodes(self, filename):

        model = load(filename, self._cfg)
        self.nodes = list(model.network.keys())

    def read_bnet_nodes(self, filename):
        self.nodes = []
        with open(filename, 'r') as bnet_model:
            for line in bnet_model:
                self.nodes.append(line.split(",")[0].strip())
             
    def get_fp_file(self):
        return os.path.join(self._path, "res_fp.csv")

    def get_probtraj_file(self):
        return os.path.join(self._path, "res_probtraj.csv")
        
    def get_statdist_file(self):
        return os.path.join(self._path, "res_statdist.csv")
        
    def write_cfg(self):
        
        with open(os.path.join(self._path, "model.cfg"), 'w+') as cfg_file:
            for param, value in self.param.items():
                cfg_file.write("%s = %s;\n" % (
                    param, value
                ))

            for node, (on, off) in self.istates.items():
                cfg_file.write("[%s].istate = %g[0], %g[1];\n" % (node, on, off))

            for node in self.nodes:
                # print(node)
                if len(self.outputs) > 0 and not node in self.outputs:
                    # print("is internal")
                    cfg_file.write("%s.is_internal = TRUE;\n" % node)
                else:
                    # print("is not internal")
                    cfg_file.write("%s.is_internal = FALSE;\n" % node)


    def write_mutations(self):
        if len(self.mutations) > 0:
            new_models = []

            os.mkdir(os.path.join(self._path, "models"))
            for model in self.models_files:
                if os.path.splitext(model)[1] == ".bnet":
                    new_models.append(self.mutate_bnet(model))
            self.models_files = new_models

    def mutate_bnet(self, model_path):
        new_path = os.path.join(self._path, "models", os.path.basename(model_path))
        with open(model_path, 'r') as model_file, open(new_path, 'w+') as new_model_file:
            for line in model_file:
                var, _ = line.split(",")
                var = var.strip()

                if var in self.mutations.keys():
                    if self.mutations[var] == 'ON':
                        new_model_file.write("%s, %d\n" % (var, 1))

                    elif self.mutations[var] == 'OFF':
                        new_model_file.write("%s, %d\n" % (var, 0))

                    else:
                        print("Unknown mutation %s for node %s. Ignored" % (self.mutations[var, var]))

                else:
                    new_model_file.write("%s\n" % line)

        return new_path



    def __del__(self):
        shutil.rmtree(self._path)