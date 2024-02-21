# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 10:34:09 2021

@author: Lavinia Ghilardi

"""

import os
import json
from gas_net.util.import_data import import_data_from_excel
from gas_net.model_nlp import buildNonLinearModel
from gas_net.modelling_library.fix_and_init_vars import init_network_default
import pyomo.environ as pyo


# paths
absolute_path = os.path.abspath(os.path.dirname(__file__))
network_data_path = absolute_path + '\\gas_net\\data\\data_files\\test\\networkData.xlsx'
input_data_path = absolute_path + '\\gas_net\\data\\data_files\\test\\inputData.xlsx'
options_path = absolute_path + '\\gas_net\\data\\Options.json'

# import data
networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
f = open(options_path)
Options = json.load(f)


#
# STEADY MODEL
# build steady model
Options['dynamic']=False
Options['T']=Options['T0']+Options['dt']/3600
m_steady = buildNonLinearModel(
        networkData, inputData, Options)

# initialization to default
m_steady = init_network_default(m_steady, p_default = 55e5)

# fix pressure source
m_steady.pSource['N0',:].fix()

# solve
ipopt = pyo.SolverFactory("ipopt")
res_steady = ipopt.solve(m_steady, tee=True)



#
# DYNAMIC MODEL
# build dynamic model
Options['dynamic']=True
Options['T']=24
m_dyn = buildNonLinearModel(
        networkData, inputData, Options)

# initialization to default
m_dyn = init_network_default(m_dyn, p_default = 55e5)

# fix pressure source
m_dyn.pSource['N0',:].fix()

# fix initial state = to steady state
t0 = m_dyn.Times.first()
for p, vol in m_dyn.Pipes_VolExtrR_interm.data():
    m_dyn.interm_p[p, vol, t0] = m_steady.interm_p[p, vol, t0]
m_dyn.interm_p[:, :, t0].fix()

# solve
ipopt = pyo.SolverFactory("ipopt")
res_dyn = ipopt.solve(m_dyn, tee=True)