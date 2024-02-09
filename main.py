# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 10:34:09 2021

@author: Lavinia Ghilardi

"""

import os
from gas_net.import_data import import_data_from_excel

# paths
absolute_path = os.path.abspath(os.path.dirname(__file__))
network_data_path = absolute_path + '\\gas_net\\data_example\\networkData.xlsx'
input_data_path = absolute_path + '\\gas_net\\data_example\\inputData.xlsx'

# import data
networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
