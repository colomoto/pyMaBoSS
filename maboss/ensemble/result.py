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
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
import numpy as np
import multiprocessing
import pandas
import matplotlib.pyplot as plt 
from re import match


class EnsembleResult(BaseResult):
  
    def __init__(self, models_files, cfg_filename, prefix="res", individual_results=False, random_sampling=False):

        self.models_files = models_files
        self._cfg = cfg_filename
        self._path = tempfile.mkdtemp()
        BaseResult.__init__(self, self._path)
        self.prefix = prefix
        self.asymptotic_probtraj_distribution = None
        self.asymptotic_nodes_probtraj_distribution = None
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

    def getSteadyStatesDistribution(self, filter=None):
        if self.asymptotic_probtraj_distribution is None:
            results = []
            for i, model in enumerate(self.models_files):
                results.append(self.getResultsFromModel(i))

            tables = []
            with multiprocessing.Pool(processes=self.get_thread_count()) as pool:
                tables = pool.starmap(getSteadyStatesSingleDistribution, [(result, i) for i, result in enumerate(results)])
            self.asymptotic_probtraj_distribution = pandas.concat(tables, axis=0, sort=False)
            self.asymptotic_probtraj_distribution.fillna(0, inplace=True)

        if filter is not None:
            return apply_filter(self.asymptotic_probtraj_distribution, filter)

        return self.asymptotic_probtraj_distribution

    def getSteadyStatesNodesDistribution(self, filter=None):
        if self.asymptotic_nodes_probtraj_distribution is None:

            table = self.getSteadyStatesDistribution()
            nodes = get_nodes(table.columns.values)
            with multiprocessing.Pool(processes=self.get_thread_count()) as pool:
                self.asymptotic_nodes_probtraj_distribution = pandas.concat(
                    pool.starmap(getSteadyStatesNodesSingleDistribution, [(table, t_index, nodes) for t_index in table.index]), 
                    sort=False, axis=0
                )

        if filter is not None:
            return apply_filter(self.asymptotic_nodes_probtraj_distribution, filter)

        return self.asymptotic_nodes_probtraj_distribution

    def filterEnsemble(self, node_filter=None, state_filter=None):
        if node_filter is not None:
            data = self.getSteadyStatesNodesDistribution(node_filter)
            return list(data.index.values)

        if state_filter is not None:
            data = self.getSteadyStatesDistribution(state_filter)
            return list(data.index.values)
        
    def createSubEnsemble(self, output_directory, node_filter=None, state_filter=None):

        sub_list = self.filterEnsemble(node_filter, state_filter)
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)

        for model in sub_list:
            shutil.copyfile(
                self.models_files[model], 
                os.path.join(output_directory, os.path.basename(self.models_files[model]))
            )
    
    def plotSteadyStatesDistribution(self, figsize=None):

        pca = PCA()
        table = self.getSteadyStatesDistribution()
        mat = table.values
        pca_res = pca.fit(mat)
        X_pca = pca.transform(mat)
        arrows_raw = (np.transpose(pca_res.components_[0:2, :]))
        self.plotPCA(pca, X_pca, list(table.columns.values), list(table.index.values) , figsize=figsize)
        
    def plotSteadyStatesNodesDistribution(self, compare=None, clusters=0, **args):

        pca = PCA()
        table = self.getSteadyStatesNodesDistribution()
        mat = table.values
        pca_res = pca.fit(mat)
        X_pca = pca.transform(mat)
        arrows_raw = (np.transpose(pca_res.components_[0:2, :]))

        colors = None
        if clusters > 0:
            kmeans = KMeans(n_clusters=clusters).fit(X_pca)
            print(kmeans.cluster_centers_)
            colors=kmeans.labels_.astype(float)



        if compare is not None:
            compare_table = compare.getSteadyStatesNodesDistribution()
            c_pca = pca.transform(compare_table.values)
            self.plotPCA(
                pca, X_pca, 
                list(table.columns.values), list(table.index.values), colors,
                compare=c_pca, **args
            )
        else:
            self.plotPCA(
                pca, X_pca, 
                list(table.columns.values), list(table.index.values), colors,
                **args
            )

    def plotPCA(self, pca, X_pca, samples, features, colors, compare=None, figsize=None, show_samples=False, show_features=True): 
        fig = plt.figure(figsize=figsize)

        if colors is None:
            plt.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.1)
        else:
            plt.scatter(X_pca[:, 0], X_pca[:, 1], c=colors, s=50, alpha=0.1)

        if compare is not None:
            plt.scatter(compare[:, 0], compare[:, 1], alpha=0.1)

        plt.xlabel("PC{} ({}%)".format(1, round(pca.explained_variance_ratio_[0] * 100, 2)))
        plt.ylabel("PC{} ({}%)".format(2, round(pca.explained_variance_ratio_[1] * 100, 2)))
                
        arrows_raw = pca.components_[0:2, :].T
        
        max_x_arrows = max(arrows_raw[:, 0])
        min_x_arrows = min(arrows_raw[:, 0])

        if compare is None:
            max_x_values = max(X_pca[:, 0])
            min_x_values = min(X_pca[:, 0])
        else:
            max_x_values = max(max(X_pca[:, 0]), max(compare[:, 0]))
            min_x_values = min(min(X_pca[:, 0]), min(compare[:, 0]))
        
        max_y_arrows = max(arrows_raw[:, 1])
        min_y_arrows = min(arrows_raw[:, 1])

        if compare is None:
            max_y_values = max(X_pca[:, 1])
            min_y_values = min(X_pca[:, 1])
        else:
            max_y_values = max(max(X_pca[:, 1]), max(compare[:, 1]))
            min_y_values = min(min(X_pca[:, 1]), min(compare[:, 1]))
  
        if show_samples:
            for i, txt in enumerate(features):
                plt.annotate(txt, (X_pca[i, 0], X_pca[i, 1]))
  
        if show_features:
            for i, v in enumerate(arrows_raw):
                plt.arrow(0, 0, v[0], v[1],  linewidth=2, color='red')
                plt.text(v[0], v[1], samples[i], color='black', ha='center', va='center', fontsize=18)

            plt.xlim(min(min_x_values, min_x_arrows)*1.2, max(max_x_values, max_x_arrows)*1.2)
            plt.ylim(min(min_y_values, min_y_arrows)*1.2, max(max_y_values, max_y_arrows)*1.2)
        else:
            plt.xlim(min_x_values*1.2, max_x_values*1.2)
            plt.ylim(min_y_values*1.2, max_y_values*1.2)

    def plotTSNESteadyStatesNodesDistribution(self, filter=None, perplexity=50, n_iter=2000, **args):

        pca = PCA()
        table = self.getSteadyStatesNodesDistribution()
        
        model = TSNE(perplexity=perplexity, n_iter=n_iter, n_iter_without_progress=n_iter*0.5)   
        res = model.fit_transform(table.values)

        if filter is None:
            fig = plt.figure(**args)
            plt.scatter(res[:, 0], res[:, 1])
        else:
            fig = plt.figure(**args)
            filtered = self.filterEnsemble(filter)
            not_filtered = list(set(range(len(self.models_files))).difference(set(filtered)))
            
            plt.scatter(res[filtered, 0], res[filtered, 1], color='r')
            plt.scatter(res[not_filtered, 0], res[not_filtered, 1], color='b')



def fix_order(string):
    return " -- ".join(sorted(string.split(" -- ")))

def getSteadyStatesSingleDistribution(result, i):
    if os.path.getsize(result.get_probtraj_file()) > 0:
        raw_table_states = result.get_last_states_probtraj()
        table_states = result.get_last_states_probtraj()
        table_states.rename(index={table_states.index[0]: i}, inplace=True)
        rename_columns = {col: fix_order(col) for col in table_states.columns}
        table_states.rename(columns=rename_columns, inplace=True)
        return table_states

def get_nodes(states):
    nodes = set()
    for s in states:
        if s != '<nil>':
            nds = s.split(' -- ')
            for nd in nds:
                nodes.add(nd)
    return nodes

def getSteadyStatesNodesSingleDistribution(table, index, nodes):
    ntable = pandas.DataFrame(np.zeros((1, len(nodes))), index=[index], columns=nodes)
    for i, row in enumerate(table):
        state = table.columns[i]
        if state != "<nil>":
            t_nodes = state.split(" -- ")
            for node in t_nodes:
                ntable.loc[index, node] += table.loc[index, state]
                
    return ntable

def apply_filter(data, filter):

    res = match(r"(\w+)\s*([<|>|==|<=|>=|!=]+)\s*(\d+[\.\d+]*)", filter)
    if res is not None:
        (species, operator, value) = res.groups()
        fun = {
            '<' : data[species] < float(value),
            '>' : data[species] > float(value),
            '==' : data[species] == float(value),
            '!=' : data[species] != float(value),
            '<=' : data[species] <= float(value),
            '>=' : data[species] >= float(value)
        }
        return data[fun[operator]]
    