from __future__ import print_function
import sys
from .results import UpdatePopulationResults

class UpdatePopulation:
    def __init__(self, model, uppfile, previous_run=None, verbose=False):

        self.model = model
        self.uppfile = uppfile
        self.previous_run = previous_run

        self.time_step = float(model.param['max_time'])
        self.time_shift = 0.0
        self.base_ratio = 1.0

        self.node_list = list(model.network.keys())
        self.division_node = ""
        self.death_node = ""

        self.update_var = {}
        self.pop_ratio = 1.0
        self.step_number = -1

        self.verbose = verbose

        if previous_run:
            # Chain the results!!
            prev_pop_ratios = previous_run.get_population_ratios()
            self.time_shift = prev_pop_ratios.last_valid_index()
            self.base_ratio = prev_pop_ratios.iloc[-1]
            self.model = model.copy()

        self._readUppFile()

    def run(self, workdir=None, overwrite=None, verbose=False):
        return UpdatePopulationResults(self, verbose, workdir, overwrite, self.previous_run)

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

        except FileNotFoundError:
            print("Cannot find .upp file", file=sys.stderr)
            exit()

    def setStepNumber(self, step_number):
        self.step_number = step_number

    def setDeathNode(self, death_node):
        self.death_node = death_node

    def setDivisionNode(self, division_node):
        self.division_node = division_node
