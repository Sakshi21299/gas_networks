# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 18:07:52 2024

@author: ssnaik
"""

import pyomo.contrib.mpc as mpc
import pyomo.environ as pyo
from idaes.core.util.model_statistics import degrees_of_freedom
from gas_net.model_nlp import buildNonLinearModel
from gas_net.modelling_library.fix_and_init_vars import init_network_default
from gas_net.examples.run_nlp_gaslib40 import run_model
from gas_net.util.make_demand_dynamic import dynamic_demand_calculation
from gas_net.util.import_data import import_data_from_excel
from gas_net.util.debug_model import debug_gas_model
from gas_net.util.plotting_util.plot_dynamic_profiles import plot_compressor_beta, plot_compressor_power
import json

def get_data_to_build_plant_model(network_path = None, 
                                  input_path = None, 
                                  options_path = None):
    if network_path is None:
        network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\networkData.xlsx'
    if input_path is None:
        input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData.xlsx'
    if options_path is None:
        options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'
    
    #Load network and input data
    networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
    
    #Load options file
    with open(options_data_path, 'r') as file:
        Options = json.load(file)
    
    Options['dynamic']=True
    Options['T']=1
    
    return networkData, inputData, Options

def make_plant_and_controller_model():
    # Get initialized dynamic model to build controller
    # The dynamic model is initialized using a sinusoidal demand profile
    # centered around the steady state demand with a horizon of 24 hours
    m_steady, m_dyn = run_model()
    m_controller = m_dyn
    
    #Make plant model 
    networkData, inputData, Options = get_data_to_build_plant_model()
    m_plant = buildNonLinearModel(networkData, inputData, Options)
    
    #Initialize plant model
    m_plant = init_network_default(m_plant, p_default = 55e5)

    # fix pressure and flow source in plant
    m_plant.pSource["source_1", :].fix()
    m_plant.pSource["source_2", :].fix()
    m_plant.wSource["source_3", :].fix()
    
    #Fix initial data to steady state 
    t0 = m_plant.Times.first()
    for p, vol in m_plant.Pipes_VolExtrR_interm.data():
        m_plant.interm_p[p, vol, t0] = m_steady.interm_p[p, vol, t0]
    m_plant.interm_p[:, :, t0].fix()
    
    #Fix plant DOF to DOF in t0 of the controller 
    for c in m_plant.Stations:
        for t in m_plant.Times:
            m_plant.compressor_P[c, t] = m_dyn.compressor_P[c, t0]
            
    m_plant.compressor_P[:, :].fix()
    m_plant.ObjFun.deactivate()
    
    assert degrees_of_freedom(m_plant) == 0
    
    #Initialize plant model by simulation
    ipopt = pyo.SolverFactory('ipopt')
    ipopt.solve(m_plant, tee = True)
    
    return m_controller, m_plant

def load_demand_data(m, demand_data, start, stop):
    for s in m.wCons:
        if s[0].startswith("sink"):
            counter = 0
            actual_demand = demand_data[s[0]][start:stop]
            for t in m.Times:
                m.wCons[s[0], 0, t].fix(actual_demand[counter])
                counter += 1
    
def run_nmpc(simulation_steps = 24, 
             sample_time = 1, 
             controller_horizon = 24, 
             plant_horizon = 1):
    #Get initialized controller and plant models
    m_controller,m_plant = make_plant_and_controller_model()
    
    #Get extended demand data
    demand_data = dynamic_demand_calculation(m_controller, extended_profile=True)
    
    #Create dynamic model interface for controller
    controller_interface = mpc.DynamicModelInterface(m_controller, m_controller.Times)
    t0_controller = m_controller.Times.first()
    
    #Create dynamic model interface for plant
    plant_interface = mpc.DynamicModelInterface(m_plant, m_plant.Times)
    
    #Define solver
    solver = pyo.SolverFactory('ipopt')
    tee = True
    
    #Variables that'll be fixed in the plant simulation
    plant_fixed_variables = [m_controller.compressor_P["compressorStation_1", :],
                         m_controller.compressor_P["compressorStation_2", :],
                         m_controller.compressor_P["compressorStation_3", :],
                         m_controller.compressor_P["compressorStation_4", :],
                         m_controller.compressor_P["compressorStation_5", :],
                         m_controller.compressor_P["compressorStation_6", :]]
    
    non_initial_plant_time = list(m_plant.Times)[1:]
    t0_controller = m_controller.Times.first()
    sim_t0 = 0.0

    #
    # Initialize data structure to hold results of "rolling horizon"
    # simulation.
    #
    sim_data = plant_interface.get_data_at_time([sim_t0])

    for i in range(simulation_steps):
        print("Running controller %d th time"%i)
        # The starting point of this part of the simulation
        # in "real" time (rather than the model's time set)
        sim_t0 = i * sample_time
        
        #Load demand data into the controller and plant
        start = sim_t0
        stop = start + controller_horizon + 1
        load_demand_data(m_controller, demand_data, start, stop)
        
        start = sim_t0
        stop = start + plant_horizon + 1
        load_demand_data(m_plant, demand_data, start, stop)
        
        #
        # Solve controller model to get inputs
        #
        assert degrees_of_freedom(m_controller) == 24*6
        res = solver.solve(m_controller, tee=tee)
        pyo.assert_optimal_termination(res)
        
        ts_data = controller_interface.get_data_at_time(sample_time)
        input_data = ts_data.extract_variables(plant_fixed_variables)
        
        plant_interface.load_data(input_data, time_points = non_initial_plant_time)
        
        #
        # Solve plant model to simulate
        #
        assert degrees_of_freedom(m_plant) == 0
        res = solver.solve(m_plant, tee=tee)
        pyo.assert_optimal_termination(res)
        
        #
        # Extract data from simulated model
        #
        m_data = plant_interface.get_data_at_time(non_initial_plant_time)
        m_data.shift_time_points(sim_t0 - m_plant.Times.first())
        sim_data.concatenate(m_data)
    
        #
        # Re-initialize plant model
        #
        tf_data = plant_interface.get_data_at_time(m_plant.Times.last())
        plant_interface.load_data(tf_data)

        #
        # Re-initialize controller model
        #
        controller_interface.shift_values_by_time(sample_time)
        controller_interface.load_data(tf_data, time_points=t0_controller)
        
    return m_plant, m_controller, sim_data
    
if __name__ =="__main__":
    m_plant, m_controller, sim_data = run_nmpc()
    
    #Plot compressor power in the plant (Note: it is scaled by 1e5)
    from pyomo.contrib.mpc.examples.cstr.model import _plot_time_indexed_variables
    _plot_time_indexed_variables(sim_data, [m_plant.compressor_P["compressorStation_1",:], 
                                            m_plant.compressor_P["compressorStation_2",:], 
                                            m_plant.compressor_P["compressorStation_3",:], 
                                            m_plant.compressor_P["compressorStation_4",:], 
                                            m_plant.compressor_P["compressorStation_5",:], 
                                            m_plant.compressor_P["compressorStation_6",:]], show=True)
    
    #All pressure variables at demand nodes
    all_nodes_p = []
    for n in m_plant.Nodes:
        if str(n).startswith('sink'):
            all_nodes_p.append(m_plant.node_p[n, :])
    _plot_time_indexed_variables(sim_data, all_nodes_p, show = True)