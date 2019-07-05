from __future__ import print_function

from ..results.baseresult import BaseResult
from ..results.storedresult import StoredResult
import os
import tempfile
import subprocess
import sys
from random import random
import shutil
from sklearn.decomposition import PCA
import numpy as np
import multiprocessing
import pandas
import matplotlib.pyplot as plt 

class EnsembleResult(BaseResult):
  
    def __init__(self, models_files, cfg_filename, prefix="res", individual_results=False, random_sampling=False):

        self.models_files = models_files
        self._cfg = cfg_filename
        self._path = tempfile.mkdtemp()
        BaseResult.__init__(self, self._path)
        self.prefix = prefix
        self.asymptotic_probtraj_distribution = None
        maboss_cmd = "MaBoSS"

        options = ["--ensemble"]
        if individual_results:
            options.append("--save-individual")

        if random_sampling:
            options.append("--random-sampling")

        cmd_line = [
            maboss_cmd, "-c", self._cfg
        ] + options + [
            "-o", self._path+'/'+self.prefix
        ] + self.models_files

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

    def get_thread_count(self):
        # TODO : Extracting it from the cfg
        return 6


    def get_fp_file(self):
        return os.path.join(self._path, "%s_fp.csv" % self.prefix)

    def get_probtraj_file(self):
        return os.path.join(self._path, "%s_probtraj.csv" % self.prefix)
        
    def get_statdist_file(self):
        return os.path.join(self._path, "%s_statdist.csv" % self.prefix)

    def getResultsFromModel(self, model):
        return StoredResult(self._path, self.prefix + "_model_" + str(model))

    def __del__(self):
        shutil.rmtree(self._path)


    def getSteadyStatesDistribution(self):

        if self.asymptotic_probtraj_distribution is None:
            results = []
            for i, model in enumerate(self.models_files):
                results.append(self.getResultsFromModel(i))

            tables = []
            with multiprocessing.Pool(processes=self.get_thread_count()) as pool:
                tables = pool.starmap(getSteadyStatesSingleDistribution, [(result, i) for i, result in enumerate(results)])
            self.asymptotic_probtraj_distribution = pandas.concat(tables, axis=1, sort=False)
            self.asymptotic_probtraj_distribution.fillna(0, inplace=True)
        return self.asymptotic_probtraj_distribution

    def plotSteadyStatesDistribution(self):

        pca = PCA()
        new_table = self.getSteadyStatesDistribution()
        mat = np.transpose(new_table.values)
        pca_res = pca.fit(mat)
        X_pca = pca.transform(mat)
        # plot principal components
        # X_pca = pca.transform(mat)
        arrows_raw = (np.transpose(pca_res.components_[0:2, :]))
        fig = plt.figure(figsize=(15, 10), dpi=500)
        plt.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.5)
        plt.xlabel("PC{} ({}%)".format(1, round(pca.explained_variance_ratio_[0] * 100, 2)))
        plt.ylabel("PC{} ({}%)".format(2, round(pca.explained_variance_ratio_[1] * 100, 2)))
        # for i, txt in enumerate(new_table.columns):
        #     plt.annotate(txt, (X_pca[i, 0], X_pca[i, 1]))
        
        max_x_arrows = max(arrows_raw[:, 0])
        min_x_arrows = min(arrows_raw[:, 0])
        max_x_values = max(X_pca[:, 0])
        min_x_values = min(X_pca[:, 0])
        min_x_ratio = min_x_values / min_x_arrows
        max_x_ratio = max_x_values / max_x_arrows
        x_ratio = min(min_x_ratio, max_x_ratio)
        
        max_y_arrows = max(arrows_raw[:, 1])
        min_y_arrows = min(arrows_raw[:, 1])
        max_y_values = max(X_pca[:, 1])
        min_y_values = min(X_pca[:, 1])
        min_y_ratio = abs(min_y_values / min_y_arrows)
        max_y_ratio = abs(max_y_values / max_y_arrows)
        y_ratio = min(min_y_ratio, max_y_ratio)
        
        arrows = [list(arrow_raw) for arrow_raw in arrows_raw]
        
        from math import log10, floor
        def round_sig(x, sig=2):
            if (x == 0.0):
                return x
            return round(x, sig - int(floor(log10(abs(x)))) - 1)
        
        values = []
        names = []
        for i, arrow_raw in enumerate(arrows_raw):
            as_list = [round(val, 2) for val in list(arrow_raw)]
            if as_list not in values:
                values.append(as_list)
                names.append([new_table.index[i]])
        
            else:
                names[values.index(as_list)].append(new_table.index[i])
        
        for i in range(len(values)):
            plt.arrow(0, 0, values[i][0] * x_ratio, values[i][1] * y_ratio, color='r', alpha=0.5)
        
            for ii, name in enumerate(names[i]):
                plt.text(values[i][0] * x_ratio + (0.05 * x_ratio), values[i][1] * y_ratio + (ii * 0.2 * y_ratio),
                         name)
def fix_order(string):
    return " -- ".join(sorted(string.split(" -- ")))

def getSteadyStatesSingleDistribution(result, i):
    if os.path.getsize(result.get_probtraj_file()) > 0:
        raw_table_states = result.get_last_states_probtraj()
        table_states = result.get_last_states_probtraj().transpose()
        table_states.rename(columns={table_states.columns[0]: ('Proba #%d' % i)}, inplace=True)
        rename_index = {index: fix_order(index) for index in table_states.index}
        table_states.rename(index=rename_index, inplace=True)
        table_states.sort_values(by=('Proba #%d' % i), inplace=True)
        return table_states
