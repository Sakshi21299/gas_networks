  # -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 11:34:39 2024

@author: ssnaik
"""

import pyomo.contrib.mpc as mpc
import pyomo.environ as pyo
from idaes.core.util.model_statistics import degrees_of_freedom
from gas_net.model_nlp import buildNonLinearModel
from gas_net.modelling_library.fix_and_init_vars import init_network_default
from gas_net.examples.run_nlp_gaslib40 import run_model
from gas_net.util.make_demand_dynamic import dynamic_demand_calculation, uncertain_demand_calculation
from gas_net.util.import_data import import_data_from_excel
from gas_net.util.debug_model import debug_gas_model, analyze_violations
from gas_net.util.plotting_util.plot_dynamic_profiles import plot_compressor_beta, plot_compressor_power
import json
import numpy as np
from gas_net.modelling_library.stability import apply_stability_constraint
from gas_net.util.write_data_to_excel import write_data_to_excel
from pyomo.common.timing import HierarchicalTimer

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


def make_plant_and_controller_model(ocss_file_path, input_data_path = None, network_data_path = None, options_data_path = None, horizon = 24, num_time_periods = 1, uncertainty = None):
    # Get initialized dynamic model to build controller
    # The dynamic model is initialized using a sinusoidal demand profile
    # centered around the steady state demand with a horizon of 24 hours
    m_steady, m_dyn = run_model(network_data_path = network_data_path, horizon = horizon, num_time_periods = num_time_periods, 
                                input_data_path=input_data_path, options_data_path=options_data_path, ocss_file_path=ocss_file_path, 
                                periodic_constraints=True, uncertainty = uncertainty)
    m_controller = m_dyn
    
    #Make plant model 
    networkData, inputData, Options = get_data_to_build_plant_model(network_data_path = network_data_path, input_data_path = input_data_path, options_data_path = options_data_path)
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
    m_plant.compressor_beta["compressorStation_1", :].setub(4)
    
    assert degrees_of_freedom(m_plant) == 0
    
    #Initialize plant model by simulation
    ipopt = pyo.SolverFactory('ipopt')
    ipopt.solve(m_plant, tee = True)
    
    return m_controller, m_plant

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
        t1 = m.controller_1.Times.at(2)
        return m.controller_1.compressor_P[c, t1] == m.controller_2.compressor_P[c, t1]
    m.non_anticipativity_con_1 = pyo.Constraint(m.controller_1.Stations, rule = _non_anticipativity_con_1)
    
    def _non_anticipativity_con_2(m, c):
        t1 = m.controller_2.Times.at(2)
        return m.controller_2.compressor_P[c, t1] == m.controller_3.compressor_P[c, t1]
    m.non_anticipativity_con_2 = pyo.Constraint(m.controller_2.Stations, rule = _non_anticipativity_con_2)

def write_multistage_enmpc_stability_constraint(m):
    #Stability parameters for the multistage ENMPC problem
    m.multistage_tracking_cost_plant_prev = pyo.Param(initialize = 1, mutable = True)
    m.multistage_lyapunov_function_prev = pyo.Param(initialize = 1, mutable = True)
    
    #Multistage enmpc lyapunov value function variable 
    m.multistage_lyapunov_function_current = pyo.Var(initialize = 1)
    def _lyapunov_function_definition_multistage(m):
        return m.multistage_lyapunov_function_current == (m.controller_1.lyapunov_function_current 
                                                         + m.controller_2.lyapunov_function_current 
                                                         + m.controller_3.lyapunov_function_current)
    m.lyapunov_function_definition_multistage = pyo.Constraint(rule = _lyapunov_function_definition_multistage)
    
    def _stability_con_multistage(m):
        m.stability_slack = pyo.Var(initialize = 0, domain = pyo.Reals)
        return 1/3*(m.multistage_lyapunov_function_current - m.multistage_lyapunov_function_prev) <= -m.multistage_tracking_cost_plant_prev + m.stability_slack
    m.multistage_stability_con = pyo.Constraint(rule = _stability_con_multistage)
    m.obj = pyo.Objective(expr = m.obj + 1e-3*m.stability_slack**2)
    return m 

def tracking_objective(m):
    m.ObjFun.deactivate()
    m.obj = pyo.Objective(expr = (sum((m.interm_p[p, vol, t] - m.interm_p_ocss[p, vol, t])**2 
                                      for p, vol in m.Pipes_VolExtrR_interm for t in m.Times if t != m.Times.last()) 
                                  + sum((m.compressor_P[s, t] - m.compressor_P_ocss[s, t])**2
                                        for s in m.Stations for t in m.Times if t != m.Times.last())
                                  + sum((m.pSource['source_3', t] - m.pSource_ocss['source_3', t])**2
                                  for t in m.Times if t != m.Times.last()))
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
    
    #Initialize hierarchical timer 
    timer = HierarchicalTimer()
    timer.start('Initialization')
    #Get initialized controller and plant models
    #Min scenario controller
    m_controller_1, m_plant = make_plant_and_controller_model(ocss_file_path = ocss_file_path_min, input_data_path = input_data_path,
                                                              network_data_path=network_data_path, options_data_path=options_data_path,
                                                              horizon = controller_horizon, num_time_periods= num_time_periods,
                                                              uncertainty={(0, 13): -0.1, (13, 25): 0.1, 
                                                                           (25, 37): -0.1, (37, 49): 0.1, 
                                                                           (49, 61): -0.1, (61, 73): 0.1,
                                                                           (73, 85): -0.1, (85, 97): 0.1,
                                                                           (97, 109): -0.1, (109, 121): 0.1,
                                                                           (121, 133): -0.1, (133, 145): 0.1})
    
    #Nominal scenario controller
    m_controller_2, _ = make_plant_and_controller_model(ocss_file_path = ocss_file_path_nominal, input_data_path = input_data_path, 
                                                        network_data_path=network_data_path, options_data_path=options_data_path,
                                                        horizon = controller_horizon, num_time_periods= num_time_periods)
    
    #Max scenario controller
    m_controller_3, _ = make_plant_and_controller_model(ocss_file_path = ocss_file_path_max, input_data_path = input_data_path, 
                                                        network_data_path=network_data_path, options_data_path=options_data_path,
                                                        horizon = controller_horizon, num_time_periods= num_time_periods,
                                                        uncertainty={(0, 13): 0.1, (13, 25): -0.1, 
                                                                     (25, 37): 0.1, (37, 49): -0.1, 
                                                                     (49, 61): 0.1, (61, 73): -0.1,
                                                                     (73, 85): 0.1, (85, 97): -0.1,
                                                                     (97, 109): 0.1, (109, 121): -0.1,
                                                                     (121, 133): 0.1, (133, 145): -0.1})
    timer.stop('Initialization')
    apply_stability_constraint(m_controller_1)
    apply_stability_constraint(m_controller_2)
    apply_stability_constraint(m_controller_3)
    
    #Create three controllers one for min, nom and max scenario each
    m = pyo.ConcreteModel()
    m.controller_1 = m_controller_1
    m.controller_2 = m_controller_2
    m.controller_3 = m_controller_3
    
    #Create a set for sink nodes to easily load demand profiles
    sink_node_set = [s for s in m.controller_1.Nodes if s.startswith("sink")]
    
    m.controller_1.sink_node_set = pyo.Set(initialize = sink_node_set)
    m.controller_2.sink_node_set = pyo.Set(initialize = sink_node_set)
    m.controller_3.sink_node_set = pyo.Set(initialize = sink_node_set)
    m_plant.sink_node_set = pyo.Set(initialize = sink_node_set)
    
    #If we need to write demand as soft constraint introduce slack variables
    #It makes sense to make actual demand a mutable parameter if we are going to write 
    #soft constraints since evry time in the controller we can just update the 
    #mutable parameter 
    m.controller_1.actual_demand = pyo.Param(m.controller_1.sink_node_set, m.controller_1.Times, initialize = 1, mutable = True)
    m.controller_2.actual_demand = pyo.Param(m.controller_2.sink_node_set, m.controller_2.Times, initialize = 1, mutable = True)
    m.controller_3.actual_demand = pyo.Param(m.controller_3.sink_node_set, m.controller_3.Times, initialize = 1, mutable = True)
    m_plant.actual_demand = pyo.Param(m_plant.sink_node_set, m_plant.Times, initialize = 1, mutable = True)
    
    soft_constraint = False
    if soft_constraint:
        write_soft_constraints(m.controller_1)
        write_soft_constraints(m.controller_2)
        write_soft_constraints(m.controller_3)
        write_soft_constraints(m_plant)
     
    # Write non-anticipativity constraints
    write_non_anticipativity_constraints(m)
    
    #Get extended demand data
    demand_data_controller_2 = dynamic_demand_calculation(m.controller_2, num_time_periods = num_time_periods, extended_profile=True)
    
    #Plant demand
    if uncertain_demand_data_plant is None:
        np.random.seed(42)
        uncertainty = np.random.uniform(low=-0.1, high=0.1, size=(73,))
        uncertainty_dict = {}
        for i in uncertainty:
            uncertainty_dict[list(uncertainty).index(i), list(uncertainty).index(i) + 1] = i
        uncertain_demand_data_plant = uncertain_demand_calculation(m.controller_2, demand_data_controller_2, 
                                                                   uncertainty=uncertainty_dict)        
        
        

    #Min scenario (-0.1, 0.1)
    demand_data_controller_1 = uncertain_demand_calculation(m.controller_1, demand_data_controller_2, 
                                                               uncertainty={(0, 13): -0.1, (13, 25): 0.1, 
                                                                            (25, 37): -0.1, (37, 49): 0.1, 
                                                                            (49, 61): -0.1, (61, 73): 0.1,
                                                                            (73, 85): -0.1, (85, 97): 0.1,
                                                                            (97, 109): -0.1, (109, 121): 0.1,
                                                                            (121, 133): -0.1, (133, 145): 0.1})
    #Max scenario (0.1, -0.1)
    demand_data_controller_3 = uncertain_demand_calculation(m.controller_3, demand_data_controller_2, 
                                                               uncertainty={(0, 13): 0.1, (13, 25): -0.1, 
                                                                            (25, 37): 0.1, (37, 49): -0.1, 
                                                                            (49, 61): 0.1, (61, 73): -0.1,
                                                                            (73, 85): 0.1, (85, 97): -0.1,
                                                                            (97, 109): 0.1, (109, 121): -0.1,
                                                                            (121, 133): 0.1, (133, 145): -0.1})
    
    
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(uncertain_demand_data_plant['sink_12'], label = 'plant demand')
    plt.title('Demand data in plant')
    plt.xlabel('time (hrs)')
    plt.ylabel('Demand (kg/s)')
    plt.legend()
    
    plt.figure()
    plt.plot(demand_data_controller_3['sink_12'][:73], '--k',label = "Max")
    plt.plot(demand_data_controller_2['sink_12'][:73], '--b',label = "Nom")
    plt.plot(demand_data_controller_1['sink_12'][:73], "--r", label = "Min")
    plt.plot(uncertain_demand_data_plant['sink_12'][:73], "g", label = 'Target demand')
    
    plt.title('Flow at sink nodes')
    plt.xlabel('Time (hrs)')
    plt.ylabel('Flow (kg/s)')
    plt.legend()
    plt.savefig('demand_mismatch.svg')
    
    #Rename the uncertain plant demand data
    demand_data_plant = uncertain_demand_data_plant
   
    #Create dynamic model interface for controller
    controller_interface_1 = mpc.DynamicModelInterface(m.controller_1, m.controller_1.Times)
    controller_interface_2 = mpc.DynamicModelInterface(m.controller_2, m.controller_2.Times)
    controller_interface_3 = mpc.DynamicModelInterface(m.controller_3, m.controller_3.Times)
    t0_controller = m.controller_1.Times.first()
    
    #Create dynamic model interface for plant
    plant_interface = mpc.DynamicModelInterface(m_plant, m_plant.Times)
    
    #Define solver
    solver = pyo.SolverFactory('ipopt')
    solver.options['tol'] = 1e-4
    tee = True
    
    #Variables that'll be fixed in the plant simulation
    plant_fixed_variables = [m.controller_1.compressor_P["compressorStation_1", :],
                         m.controller_1.compressor_P["compressorStation_2", :],
                         m.controller_1.compressor_P["compressorStation_3", :],
                         m.controller_1.compressor_P["compressorStation_4", :],
                         m.controller_1.compressor_P["compressorStation_5", :],
                         m.controller_1.compressor_P["compressorStation_6", :]]
    
    non_initial_plant_time = list(m_plant.Times)[1:]
    t0_controller = m.controller_1.Times.first()
    sim_t0 = 0.0

    #
    # Initialize data structure to hold results of "rolling horizon"
    # simulation.
    #
    sim_data = plant_interface.get_data_at_time([sim_t0])
 
    terminal_penalty_flow = {}
    terminal_penalty_pressure = {}
    
    #Economic multistage NMPC
    m.obj = pyo.Objective(expr = (m.controller_1.ObjFun + m.controller_2.ObjFun + m.controller_3.ObjFun)/3)
    m.controller_1.ObjFun.deactivate()
    m.controller_2.ObjFun.deactivate()
    m.controller_3.ObjFun.deactivate()
    
    #Tracking multistage NMPC
    # m.controller_1 = tracking_objective(m.controller_1)
    # m.controller_2 = tracking_objective(m.controller_2)
    # m.controller_3 = tracking_objective(m.controller_3)
    # m.obj = pyo.Objective(expr = (m.controller_1.obj + m.controller_2.obj + m.controller_3.obj)/3)
    # m.controller_1.obj.deactivate()
    # m.controller_2.obj.deactivate()
    # m.controller_3.obj.deactivate()
    
    controller_1_lyapunov_function = {}
    controller_2_lyapunov_function = {}
    controller_3_lyapunov_function = {}
    controller_multistage_lyapunov = {}

    # Deactivate stability constraints for individual controllers since we'll 
    # have just one stability constraint for the multistage 
    m.controller_1.stability_constraint.deactivate()
    m.controller_2.stability_constraint.deactivate()
    m.controller_3.stability_constraint.deactivate()
    m = write_multistage_enmpc_stability_constraint(m)
    
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
        load_demand_data(m.controller_1, demand_data_controller_1, start, stop, soft_constraint)
        load_demand_data(m.controller_2, demand_data_controller_2, start, stop, soft_constraint)
        load_demand_data(m.controller_3, demand_data_controller_3, start, stop, soft_constraint)
        
        start = sim_t0
        stop = start + plant_horizon + 1
        load_demand_data(m_plant, demand_data_plant, start, stop, soft_constraint)
        
        #Remove stability constraint if it is t = 0
        #Remove stability constraints if its tracking NMPC
        if sim_t0 == 0.0:
            m.multistage_stability_con.deactivate()            
        else:
            m.multistage_stability_con.activate()  
        
        #
        # Solve controller model to get inputs
        #
        timer.start('Solve_controller_model')
        res = solver.solve(m, tee=tee)
        timer.stop('Solve_controller_model')
        try:
            pyo.assert_optimal_termination(res)
        except:
            import pdb;pdb.set_trace()
            
        ts_data = controller_interface_1.get_data_at_time(sample_time)
        input_data = ts_data.extract_variables(plant_fixed_variables, context=m.controller_1)
        
        plant_interface.load_data(input_data, time_points = non_initial_plant_time)
        
        #
        # Solve plant model to simulate
        #
        timer.start('Solve_plant_model')
        res = solver.solve(m_plant, tee=tee)
        timer.stop('Solve_plant_model')
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
        controller_branches = [m.controller_1, m.controller_2, m.controller_3]
        plant_tracking_cost = 0
        for controller_model in controller_branches:
            controller_model.lyapunov_function_prev = pyo.value(controller_model.lyapunov_function_current)
            
            #Here it doesn't matter which sink node demand we look at since all sink nodes have the same demand
            plant_tracking_cost +=  pyo.value(sum((m_plant.compressor_P[s, 1.0] - controller_model.compressor_P_ocss[s, 1.0])**2 
                                                                      for s in controller_model.Stations) + 
                                                                  sum((m_plant.interm_p[p, vol, 1.0] - controller_model.interm_p_ocss[p, vol, 1.0])**2 
                                                                      for p, vol in controller_model.Pipes_VolExtrR_interm))
        m.multistage_tracking_cost_plant_prev = 1/3*(plant_tracking_cost)
            
        m.multistage_lyapunov_function_prev = pyo.value(sum(controller_model.lyapunov_function_prev for controller_model in controller_branches))
        
        controller_1_lyapunov_function[sim_t0] = pyo.value(m.controller_1.lyapunov_function_current)
        controller_2_lyapunov_function[sim_t0] = pyo.value(m.controller_2.lyapunov_function_current)
        controller_3_lyapunov_function[sim_t0] = pyo.value(m.controller_3.lyapunov_function_current)
        controller_multistage_lyapunov[sim_t0 ] = pyo.value(m.multistage_lyapunov_function_current)
        print(controller_multistage_lyapunov)
       
        
        #
        # Re-initialize controller model
        #
        controller_interface_1.shift_values_by_time(sample_time)
        controller_interface_1.load_data(tf_data, time_points=t0_controller)
        controller_interface_2.shift_values_by_time(sample_time)
        controller_interface_2.load_data(tf_data, time_points=t0_controller)
        controller_interface_3.shift_values_by_time(sample_time)
        controller_interface_3.load_data(tf_data, time_points=t0_controller)
        
        #
        # Update ocss at the last point to be equal to the first point
        #
        N = num_time_periods
        K = int(controller_horizon/num_time_periods)
        for controller_model in controller_branches:
            [controller_model.compressor_P_ocss[s, N*K].fix(controller_model.compressor_P_ocss[s, (N-1)*K]) for s in controller_model.Stations]
            [controller_model.interm_p_ocss[p, vol, N*K].fix(controller_model.interm_p_ocss[p, vol, (N-1)*K]) for p, vol in controller_model.Pipes_VolExtrR_interm]       
        
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
        write_data_to_excel(sim_data, m_plant, sheets_keys_dict, "enmpc_multistage_gaslib40_72hrs_random_scenario_explicit_terminal_constraints_avg_stability.xlsx",
                            controller_1_lyapunov=controller_1_lyapunov_function,
                            controller_2_lyapunov=controller_2_lyapunov_function,
                            controller_3_lyapunov=controller_3_lyapunov_function)
        plt.figure()
        plot_power_multistage(m.controller_1, label ="Min scenario")
        plot_power_multistage(m.controller_2, label ="Nom scenario")
        plot_power_multistage(m.controller_3, label ="Max scenario")
        plt.show()
    print(timer)
    with open('hierarchical_timer_multistage_gaslib40.txt', 'w') as f:
        f.write(str(timer))
    return m_plant, m, sim_data, controller_1_lyapunov_function, controller_2_lyapunov_function, controller_3_lyapunov_function
    
if __name__ =="__main__":
    ocss_file_path_min = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_min_scenario_extended.xlsx"
    ocss_file_path_nominal = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_extended.xlsx"
    ocss_file_path_max = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_max_scenario_extended.xlsx"
    input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData_longer_horizon.xlsx'
    network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\networkData.xlsx'
    options_data_path = r'C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\data\Options.json'

    m_plant, m_controller, sim_data, controller_1_lyapunov_function, controller_2_lyapunov_function, controller_3_lyapunov_function = run_nmpc(simulation_steps = 72, 
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
                                            m_plant.compressor_P["compressorStation_4",:], 
                                            m_plant.compressor_P["compressorStation_5",:], 
                                            m_plant.compressor_P["compressorStation_6",:]], show=True)
    
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
    write_data_to_excel(sim_data, m_plant, sheets_keys_dict, "enmpc_multistage_gaslib40_72hrs_random_scenario_explicit_terminal_constraints_avg_stability.xlsx",
                        controller_1_lyapunov=controller_1_lyapunov_function,
                        controller_2_lyapunov=controller_2_lyapunov_function,
                        controller_3_lyapunov=controller_3_lyapunov_function)
    
    # import matplotlib.pyplot as plt
    # plt.figure()
    # demand_slack = {}
    # for s in m_plant.sink_node_set:
    #     keys = m_plant.slack[s, :]
    #     for i, key in enumerate(keys):
    #         slack = sim_data.get_data_from_key(key)
      
    #     demand_slack[s]= np.sqrt(np.array(slack[1:])**2)
    #     plt.plot(demand_slack[s])
    