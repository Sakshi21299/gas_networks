# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 16:09:45 2024

@author: ssnaik
"""

# Here we will employ cyclic steady state constraints in the form of periodic constraint between 
# (N-1)K and NK: specifically z(NK) = z(N-1)K
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
from gas_net.modelling_library.stability import apply_stability_constraint
from gas_net.util.make_demand_dynamic import uncertain_demand_calculation

def get_data_to_build_plant_model(network_data_path = None, 
                                  input_data_path = None, 
                                  options_data_path = None):
    if network_data_path is None:
        network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\networkData.xlsx'
    if input_data_path is None:
        input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData.xlsx'
    if options_data_path is None:
        options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'
    
    #Load network and input data
    networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
    
    #Load options file
    with open(options_data_path, 'r') as file:
        Options = json.load(file)
    
    Options['dynamic']=True
    Options['T']=1
    
    return networkData, inputData, Options

def make_plant_and_controller_model(horizon = 24, num_time_periods = 1):
    # Get initialized dynamic model to build controller
    # The dynamic model is initialized using a sinusoidal demand profile
    # centered around the steady state demand with a horizon of 24 hours
    input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData_longer_horizon.xlsx'
    ocss_file_path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_extended.xlsx"
    m_steady, m_dyn = run_model(horizon = horizon, num_time_periods = num_time_periods, 
                                input_data_path=input_data_path, ocss_file_path=ocss_file_path, 
                                periodic_constraints=True)
    m_controller = m_dyn

    #Make plant model 
    networkData, inputData, Options = get_data_to_build_plant_model(input_data_path=input_data_path)
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

def load_demand_data(m, demand_data, start, stop, soft_constraint):
    #This function just updates the mutable parameter actual demand 
    #and if we are not writing soft constraints on demand then fixes the demand
    #to the actual demand value
    for s in m.sink_node_set:
        actual_demand = demand_data[s][start:stop]
        for t_index, t in enumerate(m.Times, start=0):
            m.actual_demand[s, t] = actual_demand[t_index]
            if not soft_constraint:   
                m.wCons[s, 0, t].fix(m.actual_demand[s, t])
    
def write_soft_constraints(m, terminal_constraints = False):
   
    m.slack = pyo.Var(m.sink_node_set, m.Times, domain = pyo.Reals)
    
    def _soft_constraint_on_demands(m, s, t):
        m.wCons[s, 0, t].unfix()
        return m.wCons[s, 0, t] == m.actual_demand[s, t] + m.slack[s, t]
    m.demand_constraint_soft = pyo.Constraint(m.sink_node_set, m.Times, rule = _soft_constraint_on_demands)
    
    m.ObjFun.deactivate() 
    
    #This differentiation is necessary because plant model doesn't have terminal constraints
    if terminal_constraints:
        m.obj = pyo.Objective(expr = m.ObjFun
                              + 1e5*sum(m.slack[s, t]**2 for s in m.sink_node_set for t in m.Times)
                              + 1e5*sum(m.terminal_flow_slacks[p, vol]**2 for p, vol in m.Pipes_VolExtrC_interm)
                              + 1e5*sum(m.terminal_pressure_slacks[p, vol]**2 for p, vol in m.Pipes_VolExtrR_interm))
    else:
        m.obj = pyo.Objective(expr = m.ObjFun
                              + 1e5*sum(m.slack[s, t]**2 for s in m.sink_node_set for t in m.Times))

def run_nmpc(simulation_steps = 24, 
             sample_time = 1, 
             controller_horizon = 24, 
             plant_horizon = 1,
             num_time_periods = 1,
             ocss_file_path = None):
    if ocss_file_path is None:
        ocss_file_path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_extended.xlsx"
    #Get initialized controller and plant models
    m_controller,m_plant = make_plant_and_controller_model(horizon = controller_horizon, num_time_periods= num_time_periods)
    apply_stability_constraint(m_controller)
    
    #Create a set for sink nodes to easily load demand profiles
    sink_node_set = [s for s in m_controller.Nodes if s.startswith("sink")]
    
    m_controller.sink_node_set = pyo.Set(initialize = sink_node_set)
    m_plant.sink_node_set = pyo.Set(initialize = sink_node_set)
    
    #If we need to write demand as soft constraint introduce slack variables
    #It makes sense to make actual demand a mutable parameter if we are going to write 
    #soft constraints since evry time in the controller we can just update the 
    #mutable parameter 
    m_controller.actual_demand = pyo.Param(m_controller.sink_node_set, m_controller.Times, initialize = 1, mutable = True)
    m_plant.actual_demand = pyo.Param(m_plant.sink_node_set, m_plant.Times, initialize = 1, mutable = True)
    soft_constraint = True
    if soft_constraint:
        write_soft_constraints(m_controller)
        write_soft_constraints(m_plant)
        
    #Get extended demand data
    #Here num time period is N which is how many times the demand profile repeats 
    demand_data = dynamic_demand_calculation(m_controller, num_time_periods = num_time_periods, extended_profile=True)
    
    uncertain_demand_data_plant = uncertain_demand_calculation(m_controller, demand_data, 
                                                               uncertainty={(0,13): 0.1, (13, 25): -0.1, 
                                                                            (25, 37): 0.1, (37, 49): -0.1, 
                                                                            (49, 61): 0.1, (61, 73): -0.1})
    
    import matplotlib.pyplot as plt
    plt.plot(demand_data['sink_12'], label= 'controller demand')
    plt.plot(uncertain_demand_data_plant['sink_12'], label = 'plant demand')
    plt.title('Demand data')
    plt.xlabel('time (hrs)')
    plt.ylabel('Demand (kg/s)')
    plt.legend()
    plt.show()
    
    #Create dynamic model interface for controller
    controller_interface = mpc.DynamicModelInterface(m_controller, m_controller.Times)
    t0_controller = m_controller.Times.first()
    
    #Create dynamic model interface for plant
    plant_interface = mpc.DynamicModelInterface(m_plant, m_plant.Times)
    
    #Define solver
    solver = pyo.SolverFactory('ipopt')
    solver.options["tol"] = 1e-4
    solver.options["linear_solver"] = "ma57"
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
    controller_lyapunov_function = {}
    for i in range(simulation_steps):
        
        print("Running controller %d th time"%i)
        # The starting point of this part of the simulation
        # in "real" time (rather than the model's time set)
        sim_t0 = i * sample_time
        
        #Load demand data into the controller and plant
        start = sim_t0
        stop = start + controller_horizon + 1
        load_demand_data(m_controller, demand_data, start, stop, soft_constraint)
        
        start = sim_t0
        stop = start + plant_horizon + 1
        load_demand_data(m_plant, uncertain_demand_data_plant, start, stop, soft_constraint)
        
        #Remove stability constraint if it is t = 0
        if sim_t0 == 0.0:
            m_controller.stability_constraint.deactivate()
            
        else:
            m_controller.stability_constraint.activate()
            
        #
        # Solve controller model to get inputs
        #
        print(degrees_of_freedom(m_controller))
        #assert degrees_of_freedom(m_controller) == 24*6 + 25*29
        res = solver.solve(m_controller, tee=tee)
        pyo.assert_optimal_termination(res)
        
        ts_data = controller_interface.get_data_at_time(sample_time)
        input_data = ts_data.extract_variables(plant_fixed_variables)
        
        plant_interface.load_data(input_data, time_points = non_initial_plant_time)
        
        #
        # Solve plant model to simulate
        #
        print(degrees_of_freedom(m_plant))
        #assert degrees_of_freedom(m_plant) == 2*29
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
        # Update the stability constraint parameters
        #
        m_controller.lyapunov_function_prev = pyo.value(m_controller.lyapunov_function_current)
        m_controller.tracking_cost_plant_prev = pyo.value(sum((m_plant.compressor_beta[s, 1.0] - m_controller.compressor_beta_ocss[s, 1.0])**2 
                                                              for s in m_controller.Stations) + 
                                                          sum((m_plant.wSource[s, 1.0] - m_controller.wSource_ocss[s, 1.0])**2 
                                                              for s in m_controller.NodesSources))
        controller_lyapunov_function[sim_t0] = pyo.value(m_controller.lyapunov_function_current)
        
        #Plot interm_p and controls for debugging
        if sim_t0 % 10 == 0:
            plt.figure()
            for s in m_controller.Stations:
                plt.plot(pyo.value(m_controller.compressor_beta[s, :]))
                plt.plot(pyo.value(m_controller.compressor_beta_ocss[s, :]), ':k')
                plt.title("At time k = %i" %int(sim_t0))
                
            plt.figure()
            for s in m_controller.NodesSources:
                plt.plot(pyo.value(m_controller.wSource[s, :]))
                plt.plot(pyo.value(m_controller.wSource_ocss[s, :]), ':k')
                plt.title("At time k = %i" %int(sim_t0))
        #
        # Re-initialize controller model
        #
        controller_interface.shift_values_by_time(sample_time)
        controller_interface.load_data(tf_data, time_points=t0_controller)
         
        #Update ocss at the last point to be equal to the first point
        N = num_time_periods
        K = int(controller_horizon/num_time_periods)
        [m_controller.compressor_beta_ocss[s, N*K].fix(m_controller.compressor_beta_ocss[s, (N-1)*K]) for s in m_controller.Stations]
        [m_controller.wSource_ocss[s, N*K].fix(m_controller.wSource_ocss[s, (N-1)*K]) for s in m_controller.NodesSources]
        #[m_controller.interm_p_ocss[p, vol, 24.0].fix(m_controller.interm_p_ocss[p, vol, 0.0]) for p, vol in m_controller.Pipes_VolExtrR_interm]       
        
        print("Lyapunov function:")
        print(controller_lyapunov_function)
    return m_plant, m_controller, sim_data, controller_lyapunov_function
    
if __name__ =="__main__":
    m_plant, m_controller, sim_data, controller_lyapunov_function = run_nmpc(simulation_steps = 72, 
                                               sample_time = 1, 
                                               controller_horizon = 72, 
                                               plant_horizon = 1,
                                               num_time_periods=3)
    
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
    _plot_time_indexed_variables(sim_data, [m_plant.interm_p['pipe_8', 2, :], m_plant.interm_p['pipe_8', 3, :], m_plant.interm_p['pipe_8', 4, :], m_plant.node_p['sink_9', :], m_plant.node_p['sink_18', :]], show = True)
    
    from gas_net.util.write_data_to_excel import write_data_to_excel
    sheets_keys_dict = {"compressor power": [m_plant.compressor_P[s, :] for s in m_plant.Stations], 
                        "compressor beta": [m_plant.compressor_beta[s, :] for s in m_plant.Stations], 
                        "wCons": [m_plant.wCons[s, 0, :] for s in m_plant.Nodes if str(s).startswith('sink')], 
                        "node pressure": all_nodes_p, 
                        "interm_w": [m_plant.interm_w[p, vol, :] for p, vol in m_plant.Pipes_VolExtrC_interm],
                        "interm_p": [m_plant.interm_p[p, vol, :] for p, vol in m_plant.Pipes_VolExtrR_interm],
                        "wSource": [m_plant.wSource[s, :] for s in m_plant.NodesSources],
                        "pSource": [m_plant.pSource[s, :] for s in m_plant.NodesSources],
                        "demand_slacks": [m_plant.slack[s, :] for s in m_plant.sink_node_set]
                        }
    write_data_to_excel(sim_data, m_plant, sheets_keys_dict, "enmpc_plantuncertainty_gaslib40_css_plus_stability_72hrs.xlsx")