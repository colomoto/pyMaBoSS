from __future__ import print_function
import sys
from .results import UpdatePopulationResults
from .cmaboss_results import CMaBoSSUpdatePopulationResults

class UpdatePopulation:
    def __init__(self, model, uppfile=None, previous_run=None, 
                 nodes_init=None, verbose=False):
        """Construct an UppMaBoss simulation
        :param model: MaBoSS model
        :param uppfile: upp file, default to None 
        :param previous_run: previous run to start from, default to None 
        :param nodes_init: dict in the form { "node1" : TrueProb1, "node2" : TrueProb2, ...}
        with nodes to be initialised to a specific value at the start
        of the simulation. These values override the previous run probabilities
        for the specified nodes, default to None 
        :param verbose: boolean to activate verbose mode, default to False
        """

        self.model = model
        self.uppfile = uppfile
        self.previous_run = previous_run
        self.nodes_init = nodes_init

        self.time_step = float(model.param['max_time'])
        self.time_shift = 0.0
        self.base_ratio = 1.0

        self.node_list = list(model.network.keys())
        self.division_node = ""
        self.death_node = ""

        self.update_var = {}
        self.nodes_formula = {}
        self.pop_ratio = 1.0
        self.step_number = -1

        self.verbose = verbose

        if previous_run:
            # Chain the results!!
            prev_pop_ratios = previous_run.get_population_ratios()
            self.time_shift = prev_pop_ratios.last_valid_index()
            self.base_ratio = prev_pop_ratios.iloc[-1]
            self.model = model.copy()

        if self.uppfile is not None:
            if "://" in self.uppfile:
                from colomoto_jupyter.io import ensure_localfile
                self.uppfile = ensure_localfile(self.uppfile)

            self._readUppFile()

    def run(self, workdir=None, overwrite=None, verbose=False, host=None, port=7777, cmaboss=False, only_final_state=False):
        if cmaboss:
            return CMaBoSSUpdatePopulationResults(self, verbose, workdir, overwrite, self.previous_run, nodes_init=self.nodes_init, only_final_state=only_final_state)
        else:
            return UpdatePopulationResults(self, verbose, workdir, overwrite, self.previous_run, host=host, port=port, nodes_init=self.nodes_init)

    def _readUppFile(self):

        try:
            with open(self.uppfile, 'r') as UPP:
                for line in UPP.readlines():
                    
                    if line.startswith("death"):
                        
                        if self.death_node != "":
                            print("Multiple definition of death node", file=sys.stderr)
                            exit()

                        self.death_node = line.split("=")[1]
                        self.death_node = self.death_node.replace(";", "").strip()
                       
                        if self.verbose:
                            print("Death node : %s" % self.death_node)

                    if line.startswith("division"):
                        
                        if self.division_node != "":
                            print("Multiple definition of division node", file=sys.stderr)
                            exit()

                        self.division_node = line.split("=")[1]
                        self.division_node = self.division_node.replace(";", "").strip()
                        
                        if self.verbose:
                            print("Division node : %s" % self.division_node)

                    if line.startswith("steps"):
                        
                        if self.step_number != -1:
                            print("Multiple definition of step number", file=sys.stderr)
                            exit()

                        self.step_number = line.split("=")[1]
                        self.step_number = int(self.step_number.replace(";", "").strip())
                        
                        if self.verbose:
                            print("Number of steps : %s" % self.step_number)
            
                    if line.startswith("$"):

                        (varName, value) = line.split("u=", 1)
                        varName = varName.strip()
                        if varName in self.update_var.keys():
                            print("Multiple definitions of %s" % varName)
                            exit()

                        value = value.replace(";", "").strip()
                        self.update_var.update({varName: value})
                        
                        if self.verbose:
                            print("Var %s updated by value %s" % (varName, value))
                            
                    if line.startswith("@"):

                        (nodeName, value) = line.split("u=", 1)
                        nodeName = nodeName.strip()[1:] # remove starting @
                        if nodeName in self.nodes_formula.keys():
                            print("Multiple formula definitions for node %s" % nodeName)
                            exit()

                        value = value.replace(";", "").strip()
                        self.nodes_formula.update({nodeName: value})
                        if self.verbose:
                            print("Node %s has formula %s" % (nodeName, value))

        except FileNotFoundError:
            print("Cannot find .upp file", file=sys.stderr)
            exit()

    def setStepNumber(self, step_number):
        self.step_number = step_number

    def setDeathNode(self, death_node):
        self.death_node = death_node

    def setDivisionNode(self, division_node):
        self.division_node = division_node

    def setExternalVariable(self, name, formula, overwrite=False):
        if name in self.update_var.keys() and not overwrite:
            print("External variable %s already exists !" % name, file=sys.stderr)
            return

        self.update_var.update({name: formula})

    def setNodeFormula(self, node, formula, overwrite=False):
        if node in self.nodes_formula.keys() and not overwrite:
            print("Formula for node %s already exists !" % node, file=sys.stderr)
            return

        self.nodes_formula.update({node: formula})
