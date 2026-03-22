# -*- coding: utf-8 -*-
"""
Created on Sun Jan 26 13:54:58 2025

@author: ssnaik
"""

from gas_net.util.import_data import import_data_from_excel
from gas_net.util.debug_model import debug_gas_model
from gas_net.util.make_demand_dynamic import dynamic_demand_calculation, uncertain_demand_calculation
from gas_net.model_nlp import buildNonLinearModel
from gas_net.modelling_library.fix_and_init_vars import init_network_default
from gas_net.util.plotting_util.plot_dynamic_profiles import plot_compressor_beta, plot_compressor_power
from gas_net.modelling_library.terminal import css_terminal_last_point, css_terminal_constraints
from idaes.core.util.model_statistics import degrees_of_freedom
import json
import pyomo.environ as pyo

def run_model(horizon = 24, num_time_periods= 1, network_data_path = None, input_data_path = None, options_data_path = None, ocss_file_path = None,
              periodic_constraints = False, calculating_css = False, uncertainty = None, source_pressure_uncertainty_factor = 1):
    if network_data_path is None:
        network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\kai_small\\networkData.xlsx'
    if input_data_path is None:
        input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\kai_small\\inputData.xlsx'
    if options_data_path is None:
        options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'
    if ocss_file_path is None:
        ocss_file_path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs.xlsx"
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
    source_pressure = pyo.value(m_steady.pSource["source_1", 0.0])
    actual_pressure = 40
    m_steady.pSource["source_1", :].fix(actual_pressure)
    
    # solve
    t0 = m_steady.Times.first()
    m_steady.compressor_beta["compressorStation_1", t0].fix(1.2)
    m_steady.compressor_beta["compressorStation_2", t0].fix(1.2)
    m_steady.compressor_beta["compressorStation_3", t0].fix(1.1)
    
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
    Options['T']=horizon
    
    m_dyn = buildNonLinearModel(
            networkData, inputData, Options)

    # initialization to default
    m_dyn = init_network_default(m_dyn, p_default = 55e5)

    # fix pressure source
    source_pressure = pyo.value(m_dyn.pSource["source_1", 0.0])
    actual_pressure = source_pressure*source_pressure_uncertainty_factor
    m_dyn.pSource["source_1", :].fix(actual_pressure)
   
    
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
    try:
        pyo.assert_optimal_termination(res_dyn)
    except:
        debug_gas_model(m_dyn)
    #Load dynamic demand profile
    
    demand_profiles = dynamic_demand_calculation(m_dyn, num_time_periods=num_time_periods)
   
    if uncertainty is not None:
        demand_profiles = uncertain_demand_calculation(m_dyn, demand_profiles, uncertainty)
        
    for s in m_dyn.wCons:
        if s[0].startswith("sink"):
            counter = 0
            for t in m_dyn.Times:
                m_dyn.wCons[s[0], 0, t].fix(demand_profiles[s[0]][counter])
                counter += 1
    
    #Add periodic terminal constraint
    
    if calculating_css:
        #If we are not calculating css then the initial state of the plant hould not be unfixed. 
        m_dyn.interm_p[:, :, t0].unfix()
        m_dyn.compressor_P[:, t0].unfix()
        m_dyn = css_terminal_constraints(m_dyn, num_time_periods= num_time_periods, horizon=horizon)
        
    if periodic_constraints:
        
        m_dyn = css_terminal_last_point(m_dyn, horizon = horizon, ocss_file_path = ocss_file_path)
        ipopt.options["tol"] = 1e-4

    from idaes.core.util.model_statistics import degrees_of_freedom
    print(degrees_of_freedom(m_dyn))

    ipopt.options["mu_init"] = 1e-6
    ipopt.options["bound_push"] = 1e-6
    res_dyn = ipopt.solve(m_dyn, tee=True)
    pyo.assert_optimal_termination(res_dyn)
    return m_steady, m_dyn

if __name__ == "__main__":
    input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\kai_small\\inputData_longer_horizon.xlsx'
    network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\kai_small\\networkData.xlsx'
    options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'
    ocss_file_path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\optimal_css_24hrs_inf_horizon.xlsx"
    
    m_steady, m_dyn = run_model(horizon = 12,
                                num_time_periods = 2, 
                                input_data_path = input_data_path, 
                                network_data_path = network_data_path, 
                                options_data_path = options_data_path, 
                                ocss_file_path = ocss_file_path,
                                calculating_css = False, 
                                periodic_constraints = False)
    
    #Plot
    plot_compressor_beta(m_dyn)
    plot_compressor_power(m_dyn)
  
    
    
    #Pipe 17, 18 has high speed
    #This doesn't happen if all the pipe diameters are set to 1
    #and the corresponding areas are also updated
    