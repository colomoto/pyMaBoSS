"""
Class that contains the cMaBoSS simulation.
"""
from .sbmlcmabossresult import SBMLCMaBoSSResult
from sys import stdout
class BNetSimulation(object):

    def __init__(self, bnet, cfgs=None):

        self.bnet = bnet
        self.cfgs = cfgs

        self.nb_nodes = self.count_nodes()
        self.cmaboss = self.get_cmaboss()

        if self.cfgs is None:
            self.cmaboss_sim = self.cmaboss.MaBoSSSim(self.bnet)
        else:
            self.cmaboss_sim = self.cmaboss.MaBoSSSim(self.bnet, self.cfgs)
   
    def count_nodes(self):
        
        res = 0
        with open(self.bnet, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if len(line) > 0 and "," in line and line.split(',')[0].strip() != "targets":
                    res += 1
        return res

    def print_bnd(self, out=stdout):
        """Produce the content of the bnd file associated to the simulation."""
        print(self.cmaboss_sim.str_bnd(), file=out)

    def print_cfg(self, out=stdout):
        """Produce the content of the cfg file associated to the simulation."""
        print(self.cmaboss_sim.str_cfg(), file=out)

    def get_cmaboss(self):

        assert self.nb_nodes <= 1024, "Models with more than 1024 nodes are not compatible with this version of MaBoSS"

        if self.nb_nodes <= 64:
            return __import__("cmaboss")
        elif self.nb_nodes <= 128:
            return __import__("cmaboss_128n")
        elif self.nb_nodes <= 256:
            return __import__("cmaboss_256n")
        elif self.nb_nodes <= 512:
            return __import__("cmaboss_512n")
        else:
            return __import__("cmaboss_1024n")

    def get_logical_rules(self):

        out = self.cmaboss_sim.get_logical_rules()    
        rules = {}
        for line in out.split("\n"):
            if ":" in line:
                node, rule = line.split(" : ", 1)
                rules.update({node.strip(): rule.strip()})

        return rules


    def run(self, only_final_state=False):
        return SBMLCMaBoSSResult(self, only_final_state)


__all__ = ["BNetSimulation"]
