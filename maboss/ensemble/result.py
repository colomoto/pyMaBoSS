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
import pandas as pd
import matplotlib.pyplot as plt 
from re import match
import ast
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class EnsembleResult(BaseResult):
  
    # def __init__(self, models_files, cfg_filename, prefix="res", individual_results=False, random_sampling=False):
    def __init__(self, simulation, workdir=None, overwrite=False, prefix="res"):

        # self._cfg = cfg_filename
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


        self._cfg = os.path.join(self._path, "ensemble.cfg")

        BaseResult.__init__(self, self._path, simulation)
        self.prefix = prefix
        self.asymptotic_probtraj_distribution = None
        self.asymptotic_nodes_probtraj_distribution = None
        maboss_cmd = simulation.get_maboss_cmd()

        simulation.write_cfg(self._path, "ensemble.cfg")
        simulation.write_models(self._path)
        self.models_files = simulation.models_files

        options = ["--ensemble"]
        if simulation.individual_results:
            options.append("--save-individual")

        if simulation.random_sampling:
            options.append("--random-sampling")

        cmd_line = [maboss_cmd] + options

        if len(simulation.individual_cfgs) > 0:
            cmd_line.append("--ensemble-istates")
            for model_file in self.models_files:
                cmd_line += ["-c", os.path.join(self._path, "models", simulation.individual_cfgs[os.path.basename(model_file)])]

        else:
            cmd_line += ["-c", self._cfg]

        cmd_line += [
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

    def load_individual_result(self, model):
        return StoredResult(self._path, self.prefix + "_model_" + str(model))

    def __del__(self):
        if self.workdir is None and os.path.exists(self._path):
            shutil.rmtree(self._path)

    def get_individual_states_probtraj(self, filter=None, cluster=None):
        if self.asymptotic_probtraj_distribution is None:
            results = []
            for i, model in enumerate(self.models_files):
                results.append(self.load_individual_result(i))

            tables = []
            with multiprocessing.Pool(processes=self.get_thread_count()) as pool:
                tables = pool.starmap(get_single_individual_states_distribution, [(result, i) for i, result in enumerate(results)])
            self.asymptotic_probtraj_distribution = pd.concat(tables, axis=0, sort=False)
            self.asymptotic_probtraj_distribution.fillna(0, inplace=True)

        if filter is not None:
            return apply_filter(self.asymptotic_probtraj_distribution, filter, state=True)

        if cluster is not None:
            return self.asymptotic_probtraj_distribution.iloc[cluster, :]
        
        return self.asymptotic_probtraj_distribution

    def get_individual_nodes_probtraj(self, filter=None, cluster=None):
        if self.asymptotic_nodes_probtraj_distribution is None:

            table = self.get_individual_states_probtraj()
            nodes = get_nodes(table.columns.values)
            with multiprocessing.Pool(processes=self.get_thread_count()) as pool:
                self.asymptotic_nodes_probtraj_distribution = pd.concat(
                    pool.starmap(get_single_individual_nodes_distribution, [(table, t_index, nodes) for t_index in table.index]), 
                    sort=False, axis=0
                )

        if filter is not None:
            return apply_filter(self.asymptotic_nodes_probtraj_distribution, filter)

        if cluster is not None:
            return self.asymptotic_nodes_probtraj_distribution.iloc[cluster, :]
        
        return self.asymptotic_nodes_probtraj_distribution

    def getByCondition(self, node_filter=None, state_filter=None):
        if node_filter is not None:
            indexes = self.get_individual_nodes_probtraj(node_filter).index.values
            labels = [0 if i not in indexes else 1 for i in range(len(self.models_files))]
            return indexes, labels
        elif state_filter is not None:
            indexes = self.get_individual_states_probtraj(state_filter).index.values
            labels = [0 if i not in indexes else 1 for i in range(len(self.models_files))]
            return indexes, labels
        

    def filterEnsembleByCondition(self, output_directory, node_filter=None, state_filter=None):

        model_list = None
        if node_filter is not None:
            model_list = self.get_individual_nodes_probtraj(node_filter).index.values
              
        elif state_filter is not None:
            model_list = self.get_individual_states_probtraj(state_filter).index.values
              
        else:
            return None

        if not os.path.exists(output_directory):
            os.mkdir(output_directory)
        else:
            shutil.rmtree(output_directory)
            os.mkdir(output_directory)

        for model in model_list:
            shutil.copyfile(
                self.models_files[int(model)], 
                os.path.join(output_directory, os.path.basename(self.models_files[int(model)]))
            )
    
    def getKMeans(self, clusters=0):
        if clusters > 0:
            kmeans = KMeans(n_clusters=clusters).fit(self.get_individual_nodes_probtraj().values)
            indices = {}
            for i, label in enumerate(kmeans.labels_):
                if label in indices.keys():
                    array = indices[label]
                    array.append(i)
                    indices.update({label: array})
                else:
                    indices.update({label: [i]})

            return indices, kmeans.labels_

    def getStatesKMeans(self, clusters=0):
        if clusters > 0:
            kmeans = KMeans(n_clusters=clusters).fit(self.get_individual_states_probtraj().values)
            indices = {}
            for i, label in enumerate(kmeans.labels_):
                if label in indices.keys():
                    array = indices[label]
                    array.append(i)
                    indices.update({label: array})
                else:
                    indices.update({label: [i]})

            return indices, kmeans.labels_

    def filterEnsembleByCluster(self, output_directory, cluster):

        if cluster is not None:
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)
            else:
                shutil.rmtree(output_directory)
                os.mkdir(output_directory)

            for model in cluster:
                shutil.copyfile(
                    self.models_files[model], 
                    os.path.join(output_directory, os.path.basename(self.models_files[model]))
                )

    def plotStates3D(self, dims, figsize=None, compare=None, ax=None, **args):
        if len(dims) == 3:
            table = self.get_individual_states_probtraj()
            
            if ax is None:
                fig = plt.figure(figsize=figsize)
                ax = fig.add_subplot(111, projection='3d')
                
            
            if compare is not None:
                
                m_table = compare.get_individual_states_probtraj()
                
                # Here we need to make sure all tables have the same columns
                all_columns = set(list(table.columns) + list(m_table.columns) + dims)
                
                for column in all_columns:
                    if column not in table.columns.values:
                        table[column] = 0
                    if column not in m_table.columns.values:
                        m_table[column] = 0
                
                table = table[all_columns]
                m_table = m_table[all_columns]
                    
                values = table[dims].values
                m_values = m_table[dims].values
                ax.scatter(values[:, 0], values[:, 1], values[:, 2], **args)
                ax.scatter(m_values[:, 0], m_values[:, 1], m_values[:, 2], **args)
            else:
                values = table[dims].values
                ax.scatter(values[:, 0], values[:, 1], values[:, 2], **args)

                
                
                
            ax.set_xlabel(dims[0])
            ax.set_ylabel(dims[1])
            ax.set_zlabel(dims[2])

    def plotSteadyStatesDistribution(self, figsize=None, compare=None, labels=None, alpha=1, **args):

        pca = PCA()
        table = self.get_individual_states_probtraj()
        if compare is not None:
            compare_table = compare.get_individual_states_probtraj()
            
            # Here we need to make sure all tables have the same columns
            all_columns = set(list(table.columns) + list(compare_table.columns))
            for column in all_columns:
                if column not in table.columns.values:
                    table[column] = 0
                if column not in compare_table.columns.values:
                    compare_table[column] = 0
            
            table = table[all_columns]
            compare_table = compare_table[all_columns]
    
            mat = table.values
            pca_res = pca.fit(mat)
            X_pca = pca.transform(mat)
            arrows_raw = (np.transpose(pca_res.components_[0:2, :]))
        
            c_pca = pca.transform(compare_table.values)
            
            self.plotPCA(
                pca, X_pca, 
                list(table.columns.values), list(table.index.values), labels, alpha,
                compare=c_pca, **args
            )
        else:
            mat = table.values
            pca_res = pca.fit(mat)
            X_pca = pca.transform(mat)
            arrows_raw = (np.transpose(pca_res.components_[0:2, :]))
        
            self.plotPCA(pca, X_pca, list(table.columns.values), list(table.index.values), labels, alpha, figsize=figsize, **args)

    def plotSteadyStatesNodesDistribution(self, compare=None, labels=None, alpha=1, **args):

        pca = PCA()
        table = self.get_individual_nodes_probtraj()
        mat = table.values
        pca_res = pca.fit(mat)
        X_pca = pca.transform(mat)
        arrows_raw = (np.transpose(pca_res.components_[0:2, :]))

        if compare is not None:
            compare_table = compare.get_individual_nodes_probtraj()
            c_pca = pca.transform(compare_table.values)
            self.plotPCA(
                pca, X_pca,
                list(table.columns.values), list(table.index.values), labels, alpha,
                compare=c_pca, **args
            )
        else:
            self.plotPCA(
                pca, X_pca,
                list(table.columns.values), list(table.index.values), labels, alpha,
                **args
            )

    def plotPCA(self, pca, X_pca, samples, features, colors=None, alpha=1, compare=None, figsize=(20, 12), show_samples=False, show_features=True, ax=None, cutoff_arrows=None):
        
        if ax is None:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(1,1,1)

        if colors is None:
            ax.scatter(X_pca[:, 0], X_pca[:, 1], alpha=alpha)
        else:
            legend = ["Cluster #%d" % (i + 1) for i in colors]

            c_colors = ["C%d" % color for color in colors]
            
            scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=c_colors, s=50, alpha=alpha, label=colors)
            import matplotlib.patches as mpatches
            # build the legend

            patches = []
            for cluster in set(colors):
                patches.append(
                    mpatches.Patch(color="C%d" % list(set(colors))[cluster], label='Cluster #%d' % (cluster + 1))
                )

            legend = plt.legend(handles=patches)

        if compare is not None:
            ax.scatter(compare[:, 0], compare[:, 1], alpha=alpha)

        ax.set_xlabel("PC{} ({}%)".format(1, round(pca.explained_variance_ratio_[0] * 100, 2)))
        ax.set_ylabel("PC{} ({}%)".format(2, round(pca.explained_variance_ratio_[1] * 100, 2)))
                
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
                ax.annotate(txt, (X_pca[i, 0], X_pca[i, 1]))
  
        if show_features:
            for i, v in enumerate(arrows_raw):
                if cutoff_arrows is None or math.sqrt(math.pow(v[0], 2) + math.pow(v[1], 2)) > cutoff_arrows:
                    ax.arrow(0, 0, v[0], v[1], linewidth=2, color='red')
                    ax.text(v[0], v[1], samples[i], color='black', ha='right', va='top', fontsize=18)

            ax.set_xlim(min(min_x_values, min_x_arrows)*1.2, max(max_x_values, max_x_arrows)*1.2)
            ax.set_ylim(min(min_y_values, min_y_arrows)*1.2, max(max_y_values, max_y_arrows)*1.2)
        else:
            ax.set_xlim(min_x_values*1.2, max_x_values*1.2)
            ax.set_ylim(min_y_values*1.2, max_y_values*1.2)

    def plotTSNESteadyStatesNodesDistribution(self, node_filter=None, state_filter=None, clusters={}, perplexity=50, n_iter=2000, **args):

        pca = PCA()
        table = self.get_individual_nodes_probtraj()
        
        model = TSNE(perplexity=perplexity, n_iter=n_iter, n_iter_without_progress=n_iter*0.5)   
        res = model.fit_transform(table.values)

        if node_filter is None and state_filter is None:
            if len(clusters) == 0:
                fig = plt.figure(**args)
                plt.scatter(res[:, 0], res[:, 1])
            else:
                fig = plt.figure(**args)
                for i, cluster in clusters.items():
                    plt.scatter(res[cluster, 0], res[cluster, 1], color="C%d" % i)

        else:
            fig = plt.figure(**args)
            filtered, _ = self.getByCondition(node_filter=node_filter, state_filter=state_filter)
            not_filtered = list(set(range(len(self.models_files))).difference(set(filtered)))
            
            plt.scatter(res[filtered, 0], res[filtered, 1], color='r')
            plt.scatter(res[not_filtered, 0], res[not_filtered, 1], color='b')

    def plotTSNESteadyStatesDistribution(self, node_filter=None, state_filter=None, clusters={}, perplexity=50, n_iter=2000, **args):

        pca = PCA()
        table = self.get_individual_states_probtraj()
        
        model = TSNE(perplexity=perplexity, n_iter=n_iter, n_iter_without_progress=n_iter*0.5)   
        res = model.fit_transform(table.values)



        if node_filter is None or state_filter is None:
            if len(clusters) == 0:
                fig = plt.figure(**args)
                plt.scatter(res[:, 0], res[:, 1])
            else:
                fig = plt.figure(**args)
                for i, cluster in clusters.items():
                    plt.scatter(res[cluster, 0], res[cluster, 1], color="C%d" % i)

        else:
            fig = plt.figure(**args)
            filtered, _ = self.getByCondition(node_filter=node_filter, state_filter=state_filter)
            not_filtered = list(set(range(len(self.models_files))).difference(set(filtered)))
            
            plt.scatter(res[filtered, 0], res[filtered, 1], color='r')
            plt.scatter(res[not_filtered, 0], res[not_filtered, 1], color='b')


def fix_order(string):
    return " -- ".join(sorted(string.split(" -- ")))

def get_single_individual_states_distribution(result, i):
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

def get_single_individual_nodes_distribution(table, index, nodes):
    ntable = pd.DataFrame(np.zeros((1, len(nodes))), index=[index], columns=nodes)
    for i, row in enumerate(table):
        state = table.columns[i]
        if state != "<nil>":
            t_nodes = state.split(" -- ")
            for node in t_nodes:
                ntable.loc[index, node] += table.loc[index, state]
                
    return ntable

def apply_filter(data, filter, state=False):

    if state: 
        filter = filter.replace(" -- ", "")
        dict_states = {column.replace(" -- ", ""): column for column in list(data.columns)}
        formula = ast.parse(filter)
        return parse_ast(formula.body[0].value, data, dict_states)
    else:
        formula = ast.parse(filter)
        return parse_ast(formula.body[0].value, data)

def parse_ast(t_ast, data, ds=None):
    if isinstance(t_ast, ast.BoolOp):
        
        if isinstance(t_ast.op, ast.And):
            
            values = [parse_ast(tt_ast, data, ds) for tt_ast in t_ast.values]
            t_data = pd.merge(values[0], values[1], how="inner", on=list(values[0].columns), left_index=True, right_index=True)

            for i in range(2, len(values)):
                t_data = pd.merge(t_data, values[i], how="inner", on=list(values[0].columns), left_index=True, right_index=True)

            return t_data
        elif isinstance(t_ast.op, ast.Or):
            
            values = [parse_ast(tt_ast, data, ds) for tt_ast in t_ast.values]
            t_data = pd.merge(values[0], values[1], how="outer", on=list(values[0].columns), left_index=True, right_index=True)

            for i in range(2, len(values)):
                t_data = pd.merge(t_data, values[i], how="outer", on=list(values[0].columns), left_index=True, right_index=True)

            return t_data
        
    elif isinstance(t_ast, ast.Compare):

        res_dict = {
            ast.Lt : data[parse_ast(t_ast.left, data, ds) < parse_ast(t_ast.comparators[0], data, ds)],
            ast.Gt : data[parse_ast(t_ast.left, data, ds) > parse_ast(t_ast.comparators[0], data, ds)],
            ast.LtE : data[parse_ast(t_ast.left, data, ds) <= parse_ast(t_ast.comparators[0], data, ds)],
            ast.GtE : data[parse_ast(t_ast.left, data, ds) >= parse_ast(t_ast.comparators[0], data, ds)],
            ast.Eq : data[parse_ast(t_ast.left, data, ds) == parse_ast(t_ast.comparators[0], data, ds)],
            ast.NotEq : data[parse_ast(t_ast.left, data, ds) != parse_ast(t_ast.comparators[0], data, ds)],
        }
        return res_dict[type(t_ast.ops[0])]

    elif isinstance(t_ast, ast.Num):
        return t_ast.n

    elif isinstance(t_ast, ast.Name):
        if ds is not None:
            if t_ast.id in ds.keys():
                return data[ds[t_ast.id]]
            else:
                return pd.Series(np.zeros(data.iloc[:, 0].shape), index=data.index)      
        else:
            return data[t_ast.id]
    
        
        
            