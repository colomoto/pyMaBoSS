from __future__ import print_function

from .result import EnsembleResult
from ..simulation import _default_parameter_list
from ..gsparser import load, _read_cfg
import os
import tempfile
import subprocess
import sys
from random import random
import shutil
import collections


class Ensemble(object):

    def __init__(self, path, cfg_filename=None, *args, **kwargs):

        self.models_path = path
        self.param = _default_parameter_list
        self.models_files = [
            os.path.join(self.models_path, file) 
            for file in os.listdir(self.models_path)
        ]
        
        self.nodes = []
        self.read_nodes(self.models_files[0])

        self._path = tempfile.mkdtemp()

        self.variables = collections.OrderedDict()
        self.istates = collections.OrderedDict()
        self.outputs = collections.OrderedDict()
        self.mutations = collections.OrderedDict()

        self._cfg = os.path.join(self._path, "model.cfg")

        if cfg_filename is not None:
            with open(cfg_filename, 'r') as cfg_file:
                variables, params, internals, istates, refstates = _read_cfg(cfg_file.read())
                self.outputs.update({node:not value for node, value in internals.items()})
                self.istates = istates

        for p in kwargs:
            if p in self.param:
                # That will keep the existing ones if unchanged
                self.param[p] = kwargs[p]
            
            elif p == "istate":
                # Here we reset it in case we have bound states
                self.istates.clear()
                self.istates.update({node: {0:val0, 1:val1} for node, (val0, val1) in kwargs[p].items()})
        
            elif p == "outputs":
                # Here we configure for all nodes, aka we reset it
                self.outputs.update({node: node in kwargs[p] for node in self.nodes})

            elif p == "mutations":
                # Here we update the existing values
                self.mutations.update(kwargs[p])

        self.write_cfg()
        self.write_mutations()

    def run(self):
        return EnsembleResult(self.models_files, self._cfg)

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

    def str_cfg(self):
        res = ""
        for var, value in self.variables.items():
            res += "%s = %s;\n" % (var, value)

        for param, value in self.param.items():
            res += "%s = %s;\n" % (param, value)

        for node, istate in self.istates.items():
            res += "[%s].istate = %g[0], %g[1];\n" % (node, istate[0], istate[1])

        for node in self.nodes:
            if len(self.outputs) > 0 and (node in self.outputs.keys() and self.outputs[node]):
                res += "%s.is_internal = FALSE;\n" % node
            else:
                res += "%s.is_internal = TRUE;\n" % node
        return res

    def print_cfg(self):
        print(self.str_cfg())

    def write_cfg(self):
        with open(self._cfg, 'w+') as cfg_file:
            cfg_file.write(self.str_cfg())
            

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
