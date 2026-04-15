from results import *
import re
import pandas as pd

def get_node_data(node_name, result_obj):
    """

    :param node_name: the name of the node we are looking for
    :param result_obj: is the file or df where the computed results are
    :return: the data where the node is
    """
    df_nodes = result_obj.get_nodes_probtraj()

    if node_name not in df_nodes.columns:
        return None

    return df_nodes[node_name]

def extract_columns_where_node_is(node_name, result_obj):
    """

    :param node_name:
    :param result_obj:
    :return:
    """

    pattern = rf"(^| -- ){re.escape(node_name)}($| -- )"
    cols = [col for col in result_obj.columns if re.search(pattern, col)]

    return result_obj[cols]

