# coding: utf-8
# MaBoSS (Markov Boolean Stochastic Simulator)
# Copyright (C) 2011-2018 Institut Curie, 26 rue d'Ulm, Paris, France

# MaBoSS is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# MaBoSS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Module: maboss/comm.py
# Authors: Eric Viara <viara@sysra.com>, Vincent Noel <contact@vincent-noel.fr>
# Date: May 2018 - February 2019

from ..results.baseresult import BaseResult
from io import StringIO
import numpy as np
import pandas as pd


class Result(BaseResult):

    def __init__(self, simulation):
        BaseResult.__init__(self, simulation)
        self._status = 0
        self._errmsg = ""
        self._stat_dist = None
        self._prob_traj = None
        self._traj = None
        self._FP = None
        self._runlog = None

    def setStatus(self, status):
        self._status = status

    def setErrorMessage(self, errmsg):
        self._errmsg = errmsg

    def setStatDist(self, data_value):
        self._stat_dist = data_value

    def setProbTraj(self, data_value):
        self._prob_traj = data_value

    def setTraj(self, data_value):
        self._traj = data_value

    def setFP(self, data_value):
        self._FP = data_value

    def setRunLog(self, data_value):
        self._runlog = data_value

    def getStatus(self):
        return self._status

    def getErrorMessage(self):
        return self._errmsg

    def getStatDist(self):
        return self._stat_dist

    def getProbTraj(self):
        return self._prob_traj

    def getTraj(self):
        return self._traj

    def getFP(self):
        return self._FP

    def getRunLog(self):
        return self._runlog

    def _get_fp_fd(self):
        return StringIO(self.getFP())

    def _get_probtraj_fd(self):
        return StringIO(self.getProbTraj())

    def _get_statdist_fd(self):
        return StringIO(self.getStatDist())

    def get_probtraj_dtypes(self):

        first_line = self.getProbTraj().split("\n", 1)[0]
        cols = first_line.split("\t")
        nb_states = int((len(cols) - 5)/3)
        dtype = {
            "Time": np.float64, "TH": np.float64, "ErrorTH": np.float64, "H": np.float64, "HD=0": np.float64,
            "State": np.str, "Proba": np.float64, "ErrorProba": np.float64
        }

        for i in range(1, nb_states):
            dtype.update({"State.%d" % i: np.str, "Proba.%d" % i: np.float64, "ErrorProba.%d" % i: np.float64})
        return dtype

    def get_fptable(self):
        """Return the content of fp.csv as a pandas dataframe."""
        if self._FP is not None:
            try:
                self.fptable = pd.read_csv(self._get_fp_fd(), "\t", skiprows=[0])

            except pd.errors.EmptyDataError:
                pass

        return self.fptable
