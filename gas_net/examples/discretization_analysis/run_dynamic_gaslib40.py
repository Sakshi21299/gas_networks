# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 14:35:33 2024

@author: ssnaik
"""

from gas_net.util.import_data import import_data_from_excel
from gas_net.util.debug_model import debug_gas_model
from gas_net.util.make_demand_dynamic import dynamic_demand_calculation
from gas_net.model_nlp import buildNonLinearModel
from gas_net.modelling_library.fix_and_init_vars import init_network_default
from gas_net.util.plotting_util.plot_dynamic_profiles import plot_compressor_beta, plot_compressor_power
import json
import pyomo.environ as pyo
from gas_net.util.import_data import set_pipe_cons_to_default

def run_model(num_elements_x):
    network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\networkData.xlsx'
    input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData.xlsx'
    options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'
    
    #Load network and input data
    networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
    
    #We need to re do the input data manipulation after changing the number of finite elements 
    #in the pipes
    for p in networkData["Pipes"].keys():
        networkData["Pipes"][p]["Nvol"] = num_elements_x
    inputData['wCons'] = set_pipe_cons_to_default(inputData['wCons'], networkData['Pipes']) 
    
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
    m_steady.pSource["source_1", :].fix()
    m_steady.pSource["source_2", :].fix()
    m_steady.wSource["source_3", :].fix()
    
    # solve
    ipopt = pyo.SolverFactory("ipopt")
    res_steady = ipopt.solve(m_steady, tee=True)

    pyo.assert_optimal_termination(res_steady)
    
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
    m_dyn.pSource["source_1", :].fix()
    m_dyn.pSource["source_2", :].fix()
    m_dyn.wSource["source_3", :].fix()

    # fix initial state = to steady state
    t0 = m_dyn.Times.first()
    for p, vol in m_dyn.Pipes_VolExtrR_interm.data():
        m_dyn.interm_p[p, vol, t0] = m_steady.interm_p[p, vol, t0]
    m_dyn.interm_p[:, :, t0].fix()
    
    #I think we need this to fix the initial state
    #Confirm with larry 
    for c in m_dyn.Stations:
        m_dyn.compressor_P[c, t0] = m_steady.compressor_P[c, t0]
    m_dyn.compressor_P[:, t0].fix()
    
    # solve
    ipopt = pyo.SolverFactory("ipopt")
    res_dyn = ipopt.solve(m_dyn, tee=True)
   
    pyo.assert_optimal_termination(res_dyn)
    
    #Load dynamic demand profile
    demand_profiles = dynamic_demand_calculation(m_dyn)
    for s in m_dyn.wCons:
        if s[0].startswith("sink"):
            counter = 0
            for t in m_dyn.Times:
                m_dyn.wCons[s[0], 0, t].fix(demand_profiles[s[0]][counter])
                counter += 1
    
    #Increase UB on compressor beta
    m_dyn.compressor_beta["compressorStation_1", :].setub(4)
    
    # solve
    ipopt = pyo.SolverFactory("ipopt")
    ipopt.options["mu_init"] = 1e-6
    ipopt.options["bound_push"] = 1e-6
    res_dyn = ipopt.solve(m_dyn, tee=True)
    pyo.assert_optimal_termination(res_dyn)
    
    #Plot
    plot_compressor_beta(m_dyn)
    plot_compressor_power(m_dyn)
    
    return m_steady, m_dyn

if __name__ == "__main__":
    objective_dynamic = []
    pressure_node_sink1 = {}
    dx_list =[2, 3, 4, 5,10]
    for num_elements in dx_list:
        m_steady, m_dyn = run_model(num_elements_x = num_elements)
        objective_dynamic.append(pyo.value(m_dyn.ObjFun))
        pressure_node_sink1[num_elements] = []
        for t in m_dyn.Times:
            pressure_node_sink1[num_elements].append(pyo.value(m_dyn.node_p['sink_1', t]))
        
    import matplotlib.pyplot as plt
    #Plot dynamic model objective value
    plt.figure()
    plt.plot(dx_list, objective_dynamic, 'o-')
    plt.title("Dynamic model objective")
    plt.xlabel("Number of finite elements in pipes")
    plt.ylabel("Objective value")
    
    plt.figure()
    for key in pressure_node_sink1.keys():
        plt.plot(pressure_node_sink1[key], label = key)
    plt.xlabel("Number of finite elements in pipes")
    plt.ylabel("Pressure at exit03 (bar)")
    plt.legend()
        

