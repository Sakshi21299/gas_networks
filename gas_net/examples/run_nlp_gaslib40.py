# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 18:17:30 2024

@author: ssnaik
"""

from gas_net.util.import_data import import_data_from_excel
from gas_net.util.debug_model import debug_gas_model
from gas_net.model_nlp import buildNonLinearModel
from gas_net.modelling_library.fix_and_init_vars import init_network_default
import json
import pyomo.environ as pyo

def run_model():
    network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\networkData.xlsx'
    input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData.xlsx'
    options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'
    
    #Load network and input data
    networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
    
    #Load options file
    with open(options_data_path, 'r') as file:
        Options = json.load(file)
    
    #
    # STEADY MODEL
    # 
    
    Options['dynamic']=False
    Options['T']=Options['T0']+Options['dt']/3600
    m_steady = buildNonLinearModel(
            networkData, inputData, Options)

    # initialization to default
    m_steady = init_network_default(m_steady, p_default = 55e5)
   
    # fix source variables
    m_steady.wSource["source_1", :].fix()
    m_steady.wSource["source_2", :].fix()
    m_steady.pSource["source_3", :].fix()
    
    # solve
    ipopt = pyo.SolverFactory("ipopt")
    res_steady = ipopt.solve(m_steady, tee=True)
    try:
        pyo.assert_optimal_termination(res_steady)
    except:
        debug_gas_model(m_steady)
    
    #
    # DYNAMIC MODEL
    #
    
    Options['dynamic']=True
    Options['T']=24
    
    m_dyn = buildNonLinearModel(
            networkData, inputData, Options)

    # initialization to default
    m_dyn = init_network_default(m_dyn, p_default = 55e5)

    # fix pressure source
    m_dyn.wSource["source_1", :].fix()
    m_dyn.wSource["source_2", :].fix()
    m_dyn.pSource["source_3", :].fix()

    # fix initial state = to steady state
    t0 = m_dyn.Times.first()
    for p, vol in m_dyn.Pipes_VolExtrR_interm.data():
        m_dyn.interm_p[p, vol, t0] = m_steady.interm_p[p, vol, t0]
    m_dyn.interm_p[:, :, t0].fix()

    # solve
    ipopt = pyo.SolverFactory("ipopt")
    res_dyn = ipopt.solve(m_dyn, tee=True)
    try:
        pyo.assert_optimal_termination(res_dyn)
    except:
        debug_gas_model(m_steady)
    return m_steady, m_dyn

if __name__ == "__main__":
    m_steady, m_dyn = run_model()