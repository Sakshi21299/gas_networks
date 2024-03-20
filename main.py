# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 10:34:09 2021

@author: Lavinia Ghilardi

"""

import os
import json
from gas_net.util.import_data import import_data_from_excel
from gas_net.model_nlp import buildNonLinearModel

# paths
absolute_path = os.path.abspath(os.path.dirname(__file__))
network_data_path = absolute_path + '\\gas_net\\data\\data_files\\GasLib_11\\networkData.xlsx'
input_data_path = absolute_path + '\\gas_net\\data\\data_files\\GasLib_11\\inputData.xlsx'
options_path = absolute_path + '\\gas_net\\data\\Options.json'

# import data
networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
f = open(options_path)
Options = json.load(f)

# build model
m = buildNonLinearModel(
        networkData, inputData, Options)


from gas_net.util.networkx_graph import graph_construction, graph_plot

G = graph_construction(networkData)


graph_plot(G, node_labels=True)