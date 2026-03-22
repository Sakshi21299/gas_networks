# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 16:41:40 2025

@author: ssnaik
"""
#Robust horizon = 2
import pyomo.contrib.mpc as mpc
import pyomo.environ as pyo
from idaes.core.util.model_statistics import degrees_of_freedom
from gas_net.model_nlp import buildNonLinearModel
from gas_net.modelling_library.fix_and_init_vars import init_network_default
from gas_net.examples.run_nlp_kai_small import run_model
from gas_net.util.make_demand_dynamic import dynamic_demand_calculation, uncertain_demand_calculation
from gas_net.util.import_data import import_data_from_excel
from gas_net.util.debug_model import debug_gas_model, analyze_violations
from gas_net.util.plotting_util.plot_dynamic_profiles import plot_compressor_beta, plot_compressor_power
import json
import numpy as np
from gas_net.modelling_library.stability import apply_stability_constraint
from gas_net.util.write_data_to_excel import write_data_to_excel
import os

def get_data_to_build_plant_model(network_data_path = None, 
                                  input_data_path = None, 
                                  options_data_path = None):
    #Load network and input data
    networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
    
    #Load options file
    with open(options_data_path, 'r') as file:
        Options = json.load(file)
    
    Options['dynamic']=True
    Options['T']=1
    
    return networkData, inputData, Options


def make_plant_and_controller_model(ocss_file_path, input_data_path = None, network_data_path = None, options_data_path = None, horizon = 24, num_time_periods = 1, uncertainty = None, source_pressure_uncertainty_factor = 1):
    # Get initialized dynamic model to build controller
    # The dynamic model is initialized using a sinusoidal demand profile
    # centered around the steady state demand with a horizon of 24 hours
    m_steady, m_dyn = run_model(network_data_path = network_data_path, horizon = horizon, num_time_periods = num_time_periods, 
                                input_data_path=input_data_path, options_data_path=options_data_path, ocss_file_path=ocss_file_path, 
                                periodic_constraints=True, uncertainty = uncertainty, source_pressure_uncertainty_factor = source_pressure_uncertainty_factor)
    m_controller = m_dyn
    
    #Make plant model 
    networkData, inputData, Options = get_data_to_build_plant_model(network_data_path = network_data_path, input_data_path = input_data_path, options_data_path = options_data_path)
    m_plant = buildNonLinearModel(networkData, inputData, Options)
    
    #Initialize plant model
    m_plant = init_network_default(m_plant, p_default = 55e5)

    # fix pressure and flow source in plant
    # fix source variables
    source_pressure = pyo.value(m_plant.pSource["source_1", 0.0])
    actual_pressure = source_pressure*source_pressure_uncertainty_factor
    m_plant.pSource["source_1", :].fix(actual_pressure)
   
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

def make_controller_model(input_data_path,
                          network_data_path, 
                          options_data_path,
                          horizon, 
                          num_time_periods):
    
    #Demand uncertainty is the first uncertain parameter
    demand_uncertainty_min = {(0, 7): 0, (7, 13): -5, 
                              (13, 31): 0, (31, 37): -5, 
                              (37, 55): 0, (55, 61): -5,
                              (61, 79): 0, (79, 85): -5,
                              (85, 103): 0, (103, 109): -5,
                              (109,127): 0, (127, 133): -5,
                              (133, 145): 0}
    
    demand_uncertainty_nom = None
    
    demand_uncertainty_max = {(0, 7): 0, (7, 13): 5, 
                              (13, 31): 0, (31, 37): 5, 
                              (37, 55): 0, (55, 61): 5,
                              (61, 79): 0, (79, 85): 5,
                              (85, 103): 0, (103, 109): 5,
                              (109,127): 0, (127, 133): 5,
                              (133, 145): 0}
    
    #Supply pressure uncertainty is the second uncertain parameter
    source_pressure_uncertainty_min = 0.85
    source_pressure_uncertainty_nom = 1
    source_pressure_uncertainty_max = 1.15
    
    #Optimal cyclic steady state files
    ocss_path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\ocss_multiple_params_kai_small"
    
    ocss_min_min = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_min_min_scenario.xlsx")
    ocss_min_nom = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_min_nom_scenario.xlsx")
    ocss_min_max = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_min_max_scenario.xlsx")
    
    ocss_nom_min = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_nom_min_scenario.xlsx")
    ocss_nom_nom = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_nom_nom_scenario.xlsx")
    ocss_nom_max = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_nom_max_scenario.xlsx")
    
    ocss_max_min = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_max_min_scenario.xlsx")
    ocss_max_nom = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_max_nom_scenario.xlsx")
    ocss_max_max = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_max_max_scenario.xlsx")
    
    #Make controller models 
    #Min demand scenario
    controller_min_min, _ = make_plant_and_controller_model(ocss_min_min,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_min, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_min)
    
    controller_min_nom, _ = make_plant_and_controller_model(ocss_min_nom,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_min, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_nom)
    
    controller_min_max, _ = make_plant_and_controller_model(ocss_min_max,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_min, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_max)
    
    #Nominal demand scenario
    controller_nom_min, _ = make_plant_and_controller_model(ocss_nom_min,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_nom, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_min)
    
    controller_nom_nom, m_plant = make_plant_and_controller_model(ocss_nom_nom,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_nom, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_nom)
    
    controller_nom_max, _ = make_plant_and_controller_model(ocss_nom_max,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_nom, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_max)
    
    #Max demand scenario
    controller_max_min, _ = make_plant_and_controller_model(ocss_max_min,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_max, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_min)
    
    controller_max_nom, _ = make_plant_and_controller_model(ocss_max_nom,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_max, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_nom)
    
    controller_max_max, _ = make_plant_and_controller_model(ocss_max_max,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_max, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_max)
    
    return controller_min_min, controller_min_nom, controller_min_max, controller_nom_min, controller_nom_nom, controller_nom_max, controller_max_min, controller_max_nom, controller_max_max, m_plant
    
    
def load_demand_data(m, demand_data, start, stop, soft_constraint = False):
    #This function just updates the mutable parameter actual demand 
    #and if we are not writing soft constraints on demand then fixes the demand
    #to the actual demand value
    for s in m.sink_node_set:
        actual_demand = demand_data[s][start:stop]
        for t_index, t in enumerate(m.Times, start=0):
            m.actual_demand[s, t] = actual_demand[t_index]
            if not soft_constraint:   
                m.wCons[s, 0, t].fix(m.actual_demand[s, t])
            
def write_soft_constraints(m, terminal_constraints=False):
    m.slack = pyo.Var(m.sink_node_set, m.Times, domain = pyo.Reals)
    
    def _soft_constraint_on_demands(m, s, t):
        m.wCons[s, 0, t].unfix()
        return m.wCons[s, 0, t] == m.actual_demand[s, t] + m.slack[s, t]
    m.demand_constraint_soft = pyo.Constraint(m.sink_node_set, m.Times, rule = _soft_constraint_on_demands)
    
    m.ObjFun.deactivate() 
    #This differentiation is necessary because plant model doesn't have terminal constraints
    if terminal_constraints:
        m.obj = pyo.Objective(expr = m.ObjFun
                              + 1e3*sum(m.slack[s, t]**2 for s in m.sink_node_set for t in m.Times)
                              + 1e1*sum(m.terminal_flow_slacks[p, vol]**2 for p, vol in m.Pipes_VolExtrC_interm)
                              + 1e1*sum(m.terminal_pressure_slacks[p, vol]**2 for p, vol in m.Pipes_VolExtrR_interm))
    else:
        m.obj = pyo.Objective(expr = m.ObjFun
                              + 1e5*sum(m.slack[s, t]**2 for s in m.sink_node_set for t in m.Times))

def write_non_anticipativity_constraints(m):
    def _non_anticipativity_con_1(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_min_nom.compressor_P[c, t1]
    m.non_anticipativity_con_1 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_1)
    
    def _non_anticipativity_con_2(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_min_max.compressor_P[c, t1]
    m.non_anticipativity_con_2 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_2)
    
    def _non_anticipativity_con_3(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_nom_min.compressor_P[c, t1]
    m.non_anticipativity_con_3 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_3)
    
    def _non_anticipativity_con_4(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_nom_nom.compressor_P[c, t1]
    m.non_anticipativity_con_4 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_4)
    
    def _non_anticipativity_con_5(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_nom_max.compressor_P[c, t1]
    m.non_anticipativity_con_5 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_5)
    
    def _non_anticipativity_con_6(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_max_min.compressor_P[c, t1]
    m.non_anticipativity_con_6 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_6)
    
    def _non_anticipativity_con_7(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_max_nom.compressor_P[c, t1]
    m.non_anticipativity_con_7 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_7)
    
    def _non_anticipativity_con_8(m, c):
        t1 = m.controller_min_min.Times.at(2)
        return m.controller_min_min.compressor_P[c, t1] == m.controller_max_max.compressor_P[c, t1]
    m.non_anticipativity_con_8 = pyo.Constraint(m.controller_min_min.Stations, rule = _non_anticipativity_con_8)



def write_multistage_enmpc_stability_constraint(m, controller_models):
    #Stability parameters for the multistage ENMPC problem
    m.multistage_tracking_cost_plant_prev = pyo.Param(initialize = 1, mutable = True)
    m.multistage_lyapunov_function_prev = pyo.Param(initialize = 1, mutable = True)
    
    #Multistage enmpc lyapunov value function variable 
    m.multistage_lyapunov_function_current = pyo.Var(initialize = 1)
    def _lyapunov_function_definition_multistage(m):
        return m.multistage_lyapunov_function_current == (sum(model.lyapunov_function_current for model in controller_models))
    m.lyapunov_function_definition_multistage = pyo.Constraint(rule = _lyapunov_function_definition_multistage)
    
    def _stability_con_multistage(m):
        m.stability_slack = pyo.Var(initialize = 0, domain = pyo.Reals)
        return 1/len(controller_models)*(m.multistage_lyapunov_function_current - m.multistage_lyapunov_function_prev) <= -m.multistage_tracking_cost_plant_prev + m.stability_slack
    m.multistage_stability_con = pyo.Constraint(rule = _stability_con_multistage)
    
    m.obj = pyo.Objective(expr = m.obj + 1e-3*m.stability_slack**2)
    return m 

def tracking_objective(m):
    m.ObjFun.deactivate()
    m.obj = pyo.Objective(expr = (sum((m.interm_p[p, vol, t] - m.interm_p_ocss[p, vol, t])**2 
                                      for p, vol in m.Pipes_VolExtrR_interm for t in m.Times if t != m.Times.last()) 
                                  + sum((m.compressor_P[s, t] - m.compressor_P_ocss[s, t])**2
                                        for s in m.Stations for t in m.Times if t != m.Times.last())
                                  )
                          )
    return m

def plot_power_multistage(m, label ="no label"):
    import matplotlib.pyplot as plt
    power = []
    for t in m.Times:
        power.append(sum(pyo.value(m.compressor_P[c, t]) for c in m.Stations))
    
    plt.plot(power, label = label)
    plt.xlabel("Time (hrs)")
    plt.ylabel("Compressor Power (kWh)")
    plt.legend()
    
def run_nmpc(simulation_steps = 24, 
             sample_time = 1, 
             controller_horizon = 24, 
             plant_horizon = 1,
             num_time_periods = 1, 
             uncertain_demand_data_plant = None,
             ocss_file_path_min = None,
             ocss_file_path_nominal = None,
             ocss_file_path_max = None, 
             input_data_path = None, 
             network_data_path = None, 
             options_data_path = None):
    
    #Get initialized controller and plant models
    controller_min_min, controller_min_nom, controller_min_max, controller_nom_min, controller_nom_nom, controller_nom_max, controller_max_min, controller_max_nom, controller_max_max, m_plant = make_controller_model(input_data_path = input_data_path, 
                          network_data_path = network_data_path, 
                          options_data_path = options_data_path, 
                          horizon = controller_horizon, 
                          num_time_periods = num_time_periods)
    
    #Create three controllers one for min, nom and max scenario each
    m = pyo.ConcreteModel()
    m.controller_min_min = controller_min_min
    m.controller_min_nom = controller_min_nom
    m.controller_min_max = controller_min_max
    
    m.controller_nom_min = controller_nom_min
    m.controller_nom_nom = controller_nom_nom
    m.controller_nom_max = controller_nom_max
    
    m.controller_max_min = controller_max_min
    m.controller_max_nom = controller_max_nom
    m.controller_max_max = controller_max_max
    
    controller_models = [m.controller_min_min, m.controller_min_nom, m.controller_min_max, m.controller_nom_min, m.controller_nom_nom, m.controller_nom_max, m.controller_max_min, m.controller_max_nom, m.controller_max_max]
    
    #Create a set for sink nodes to easily load demand profiles
    sink_node_set = [s for s in m.controller_min_min.Nodes if s.startswith("sink")]
    
    
    for model in controller_models:
        #Apply stability constraints
        apply_stability_constraint(model)
        
        #Create sink set for each controller
        model.sink_node_set = pyo.Set(initialize = sink_node_set)
        
        #Create actual demand parameter
        model.actual_demand = pyo.Param(model.sink_node_set, model.Times, initialize = 1, mutable = True)
    
    m_plant.sink_node_set = pyo.Set(initialize = sink_node_set)
    m_plant.actual_demand = pyo.Param(m_plant.sink_node_set, m_plant.Times, initialize = 1, mutable = True)
     
    # Write non-anticipativity constraints
    write_non_anticipativity_constraints(m)
    
    #Get extended demand data
    demand_data_controller_nom = dynamic_demand_calculation(m.controller_nom_nom, num_time_periods = num_time_periods, extended_profile=True)
    
    #Plant demand
    np.random.seed(100)
    uncertainty = np.random.uniform(low=-5, high=5, size=(73,))
    uncertainty_dict = {}
    for i in uncertainty:
        if (list(uncertainty).index(i) > 6 and list(uncertainty).index(i) < 12) or (list(uncertainty).index(i) > 30 and list(uncertainty).index(i) < 36) or (list(uncertainty).index(i) > 54 and list(uncertainty).index(i) < 60):
            uncertainty_dict[list(uncertainty).index(i), list(uncertainty).index(i) + 1] = i
        else:
            uncertainty_dict[list(uncertainty).index(i), list(uncertainty).index(i) + 1] = 0
    uncertain_demand_data_plant = uncertain_demand_calculation(m.controller_nom_nom, demand_data_controller_nom, 
                                                               uncertainty=uncertainty_dict)
        
        

    #Min scenario 
    demand_data_controller_min = uncertain_demand_calculation(m.controller_min_nom, demand_data_controller_nom, 
                                                               uncertainty={(0, 7): 0, (7, 13): -5, 
                                                                            (13, 31): 0, (31, 37): -5, 
                                                                            (37, 55): 0, (55, 61): -5,
                                                                            (61, 79): 0, (79, 85): -5,
                                                                            (85, 103): 0, (103, 109): -5,
                                                                            (109,127): 0, (127, 133): -5,
                                                                            (133, 145): 0})
    #Max scenario
    demand_data_controller_max = uncertain_demand_calculation(m.controller_max_nom, demand_data_controller_nom, 
                                                               uncertainty={(0, 7): 0, (7, 13): 5, 
                                                                            (13, 31): 0, (31, 37): 5, 
                                                                            (37, 55): 0, (55, 61): 5,
                                                                            (61, 79): 0, (79, 85): 5,
                                                                            (85, 103): 0, (103, 109): 5,
                                                                            (109,127): 0, (127, 133): 5,
                                                                            (133, 145): 0})
    
    #Uncertain source pressure in plant
    uncertain_source_pressure_factor = np.random.uniform(low=0.85, high=1.15, size=(73,))
    # Nominal supply pressure 
    nominal_source_pressure = pyo.value(m.controller_nom_nom.pSource["source_1", 0.0])
    plant_uncertain_source_pressure = nominal_source_pressure*uncertain_source_pressure_factor
    
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(uncertain_demand_data_plant['sink_1'], label = 'plant demand')
    plt.title('Demand data in plant')
    plt.xlabel('time (hrs)')
    plt.ylabel('Demand (kg/s)')
    plt.legend()
    
    plt.figure()
    plt.plot(demand_data_controller_max['sink_1'][:73], '--k',label = "Max")
    plt.plot(demand_data_controller_nom['sink_1'][:73], '--b',label = "Nom")
    plt.plot(demand_data_controller_min['sink_1'][:73], "--r", label = "Min")
    plt.plot(uncertain_demand_data_plant['sink_1'][:73], "g", label = 'Target demand')
    
    plt.title('Flow at sink nodes')
    plt.xlabel('Time (hrs)')
    plt.ylabel('Flow (kg/s)')
    plt.legend()
    
    #Rename the uncertain plant demand data
    demand_data_plant = uncertain_demand_data_plant
   
    #Create dynamic model interface for controller
    controller_interface_min_min = mpc.DynamicModelInterface(m.controller_min_min, m.controller_min_min.Times)
    controller_interface_min_nom = mpc.DynamicModelInterface(m.controller_min_nom, m.controller_min_nom.Times)
    controller_interface_min_max = mpc.DynamicModelInterface(m.controller_min_max, m.controller_min_max.Times)
    
    controller_interface_nom_min = mpc.DynamicModelInterface(m.controller_nom_min, m.controller_nom_min.Times)
    controller_interface_nom_nom = mpc.DynamicModelInterface(m.controller_nom_nom, m.controller_nom_nom.Times)
    controller_interface_nom_max = mpc.DynamicModelInterface(m.controller_nom_max, m.controller_nom_max.Times)
    
    controller_interface_max_min = mpc.DynamicModelInterface(m.controller_max_min, m.controller_max_min.Times)
    controller_interface_max_nom = mpc.DynamicModelInterface(m.controller_max_nom, m.controller_max_nom.Times)
    controller_interface_max_max = mpc.DynamicModelInterface(m.controller_max_max, m.controller_max_max.Times)
    controller_interfaces = [controller_interface_min_min, controller_interface_min_nom, controller_interface_min_max,
                             controller_interface_nom_min, controller_interface_nom_nom, controller_interface_nom_max, 
                             controller_interface_max_min, controller_interface_max_nom, controller_interface_max_max]
    
    t0_controller = m.controller_min_min.Times.first()
    
    #Create dynamic model interface for plant
    plant_interface = mpc.DynamicModelInterface(m_plant, m_plant.Times)
    
    #Define solver
    solver = pyo.SolverFactory('ipopt')
    solver.options['tol'] = 1e-4
    tee = True
    
    #Variables that'll be fixed in the plant simulation
    plant_fixed_variables = [m.controller_min_min.compressor_P["compressorStation_1", :],
                         m.controller_min_min.compressor_P["compressorStation_2", :],
                         m.controller_min_min.compressor_P["compressorStation_3", :]
                         ]
    
    non_initial_plant_time = list(m_plant.Times)[1:]
    t0_controller = m.controller_min_min.Times.first()
    sim_t0 = 0.0

    #
    # Initialize data structure to hold results of "rolling horizon"
    # simulation.
    #
    sim_data = plant_interface.get_data_at_time([sim_t0])
 
    terminal_penalty_flow = {}
    terminal_penalty_pressure = {}
    
    #Economic multistage NMPC
    m.obj = pyo.Objective(expr = (sum(model.ObjFun for model in controller_models))/len(controller_models))
    
    for model in controller_models:
        #Deactivate objective function
        model.ObjFun.deactivate()
        
        # Deactivate stability constraints for individual controllers since we'll 
        # have just one stability constraint for the multistage
        model.stability_constraint.deactivate()
    
    controller_multistage_lyapunov = {}

    m = write_multistage_enmpc_stability_constraint(m, controller_models)

    #Test this -- Does the multistage ENMPC run if you don't have the stability constraint and 
    # Set the last period explicitly to OCSS?
    #m.multistage_stability_con.deactivate()
    
    for i in range(simulation_steps):
        print("Running controller %d th time"%i)
        # The starting point of this part of the simulation
        # in "real" time (rather than the model's time set)
        sim_t0 = i * sample_time
        
        #Load demand data into the controller and plant
        start = sim_t0
        stop = start + controller_horizon + 1
        load_demand_data(m.controller_min_min, demand_data_controller_min, start, stop)
        load_demand_data(m.controller_min_nom, demand_data_controller_min, start, stop)
        load_demand_data(m.controller_min_max, demand_data_controller_min, start, stop)
        
        load_demand_data(m.controller_nom_min, demand_data_controller_nom, start, stop)
        load_demand_data(m.controller_nom_nom, demand_data_controller_nom, start, stop)
        load_demand_data(m.controller_nom_max, demand_data_controller_nom, start, stop)
        
        load_demand_data(m.controller_max_min, demand_data_controller_max, start, stop)
        load_demand_data(m.controller_max_nom, demand_data_controller_max, start, stop)
        load_demand_data(m.controller_max_max, demand_data_controller_max, start, stop)
        
        start = sim_t0
        stop = start + plant_horizon + 1
        load_demand_data(m_plant, demand_data_plant, start, stop)
        
        #Remove stability constraint if it is t = 0
        #Remove stability constraints if its tracking NMPC
        if sim_t0 == 0.0:
            m.multistage_stability_con.deactivate()            
        else:
            m.multistage_stability_con.activate()  
        
        #
        # Solve controller model to get inputs
        #
       
        res = solver.solve(m, tee=tee)
        try:
            pyo.assert_optimal_termination(res)
        except:
            import pdb;pdb.set_trace()
        
        ts_data = controller_interface_min_min.get_data_at_time(sample_time)
        input_data = ts_data.extract_variables(plant_fixed_variables, context=m.controller_min_min)
        
        plant_interface.load_data(input_data, time_points = non_initial_plant_time)
        
        m_plant.pSource["source_1", non_initial_plant_time].fix(plant_uncertain_source_pressure[start + 1])
        
        #
        # Solve plant model to simulate
        #
       
        res = solver.solve(m_plant, tee=tee)
        try:
            pyo.assert_optimal_termination(res)
        except:
            import pdb;pdb.set_trace()
        
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
        plant_tracking_cost = 0
        for model in controller_models:
            model.lyapunov_function_prev = pyo.value(model.lyapunov_function_current)
            
            #Here it doesn't matter which sink node demand we look at since all sink nodes have the same demand
            plant_tracking_cost +=  pyo.value(sum((m_plant.compressor_P[s, 1.0] - model.compressor_P_ocss[s, 1.0])**2 
                                                                      for s in model.Stations) + 
                                                                  sum((m_plant.interm_p[p, vol, 1.0] - model.interm_p_ocss[p, vol, 1.0])**2 
                                                                      for p, vol in model.Pipes_VolExtrR_interm))
        m.multistage_tracking_cost_plant_prev = 1/len(controller_models)*(plant_tracking_cost)
            
        m.multistage_lyapunov_function_prev = pyo.value(sum(model.lyapunov_function_prev for model in controller_models))
        
        controller_multistage_lyapunov[sim_t0] = pyo.value(m.multistage_lyapunov_function_current)
        print(controller_multistage_lyapunov)
       
        #
        # Re-initialize controller model
        #
        for interface in controller_interfaces:
            interface.shift_values_by_time(sample_time)
            interface.load_data(tf_data, time_points=t0_controller)
        
        #
        # Update ocss at the last point to be equal to the first point
        #
        N = num_time_periods
        K = int(controller_horizon/num_time_periods)
        for model in controller_models:
            [model.compressor_P_ocss[s, N*K].fix(model.compressor_P_ocss[s, (N-1)*K]) for s in model.Stations]
            [model.interm_p_ocss[p, vol, N*K].fix(model.interm_p_ocss[p, vol, (N-1)*K]) for p, vol in model.Pipes_VolExtrR_interm]       
        
        #All pressure variables at demand nodes
        all_nodes_p = []
        for n in m_plant.Nodes:
            if str(n).startswith('sink'):
                all_nodes_p.append(m_plant.node_p[n, :])
        
        sheets_keys_dict = {"compressor power": [m_plant.compressor_P[s, :] for s in m_plant.Stations], 
                           "compressor beta": [m_plant.compressor_beta[s, :] for s in m_plant.Stations], 
                           "wCons": [m_plant.wCons[s, 0, :] for s in m_plant.Nodes if str(s).startswith('sink')], 
                           "node pressure": all_nodes_p, 
                           "interm_w": [m_plant.interm_w[p, vol, :] for p, vol in m_plant.Pipes_VolExtrC_interm],
                           "interm_p": [m_plant.interm_p[p, vol, :] for p, vol in m_plant.Pipes_VolExtrR_interm],
                           "wSource": [m_plant.wSource[s, :] for s in m_plant.NodesSources],
                           "pSource": [m_plant.pSource[s, :] for s in m_plant.NodesSources]
                           }
        write_data_to_excel(sim_data, m_plant, sheets_keys_dict, "enmpc_multistage_kai_72hrs_random_scenario_explicit_terminal_constraints_avg_stability.xlsx",
                            controller_1_lyapunov=controller_multistage_lyapunov)
       
    return m_plant, m, sim_data
    
if __name__ =="__main__":
    ocss_file_path_min = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_kai_small_min_scenario.xlsx"
    ocss_file_path_nominal = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_kai_small.xlsx"
    ocss_file_path_max = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_kai_small_max_scenario.xlsx"
    input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\kai_small\\inputData_longer_horizon.xlsx'
    network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\kai_small\\networkData.xlsx'
    options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'

    m_plant, m_controller, sim_data = run_nmpc(simulation_steps = 72, 
                 sample_time = 1, 
                 controller_horizon = 72, 
                 plant_horizon = 1,
                 num_time_periods=3,
                 uncertain_demand_data_plant = None,
                 ocss_file_path_min = ocss_file_path_min,
                 ocss_file_path_nominal = ocss_file_path_nominal,
                 ocss_file_path_max = ocss_file_path_max, 
                 input_data_path = input_data_path,
                 network_data_path = network_data_path,
                 options_data_path = options_data_path)
    
    #Plot compressor power in the plant (Note: it is scaled by 1e5)
    from pyomo.contrib.mpc.examples.cstr.model import _plot_time_indexed_variables
    _plot_time_indexed_variables(sim_data, [m_plant.compressor_P["compressorStation_1",:], 
                                            m_plant.compressor_P["compressorStation_2",:], 
                                            m_plant.compressor_P["compressorStation_3",:], 
                                            ], show=True)
    
    #All pressure variables at demand nodes
    all_nodes_p = []
    for n in m_plant.Nodes:
        if str(n).startswith('sink'):
            all_nodes_p.append(m_plant.node_p[n, :])
    _plot_time_indexed_variables(sim_data, all_nodes_p, show = True)
    
    _plot_time_indexed_variables(sim_data, [m_plant.wCons[s, 0, :] for s in m_plant.sink_node_set])
    
    from gas_net.util.write_data_to_excel import write_data_to_excel
    sheets_keys_dict = {"compressor power": [m_plant.compressor_P[s, :] for s in m_plant.Stations], 
                       "compressor beta": [m_plant.compressor_beta[s, :] for s in m_plant.Stations], 
                       "wCons": [m_plant.wCons[s, 0, :] for s in m_plant.Nodes if str(s).startswith('sink')], 
                       "node pressure": all_nodes_p, 
                       "interm_w": [m_plant.interm_w[p, vol, :] for p, vol in m_plant.Pipes_VolExtrC_interm],
                       "interm_p": [m_plant.interm_p[p, vol, :] for p, vol in m_plant.Pipes_VolExtrR_interm],
                       "wSource": [m_plant.wSource[s, :] for s in m_plant.NodesSources],
                       "pSource": [m_plant.pSource[s, :] for s in m_plant.NodesSources]
                       }
    write_data_to_excel(sim_data, m_plant, sheets_keys_dict, "enmpc_multistage_kai_small_multiple_uncertain_params_72hrs_random_scenario_explicit_terminal_constraints_avg_stability_1.xlsx",
                        )
    
    # import matplotlib.pyplot as plt
    # plt.figure()
    # demand_slack = {}
    # for s in m_plant.sink_node_set:
    #     keys = m_plant.slack[s, :]
    #     for i, key in enumerate(keys):
    #         slack = sim_data.get_data_from_key(key)
      
    #     demand_slack[s]= np.sqrt(np.array(slack[1:])**2)
    #     plt.plot(demand_slack[s])
    