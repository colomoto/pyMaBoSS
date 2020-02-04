"""
Class that contains the cMaBoSS simulation.
"""
from .cmabossresult2 import CMaBoSSResult2

class CMaBoSSSimulation(object):

    def __init__(self, bnd, cfgs):

        self.bnd = bnd
        self.cfgs = cfgs

        self.nb_nodes = self.count_nodes()
        self.cmaboss = self.get_cmaboss()

        self.cmaboss_net = self.cmaboss.MaBoSSNet(self.bnd)
        self.cmaboss_cfg = self.cmaboss.MaBoSSCfg(self.cmaboss_net, self.cfgs)
        
    def count_nodes(self):
        
        res = 0
        with open(self.bnd, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.lower().startswith("node"):
                    res += 1
        return res


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

    def run(self, workdir=None, only_final_state=False):
        return CMaBoSSResult2(self, workdir, only_final_state)


__all__ = ["CMaBoSSSimulation"]
