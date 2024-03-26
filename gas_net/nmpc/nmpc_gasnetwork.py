# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 16:37:31 2023

@author: Lavinia
"""
import copy
from nmpc_examples.nmpc.model_helper import DynamicModelHelper
import pyomo.environ as pyo

######################## AUXILIARY FUNCTIONS #####################################
###############################################################################
# function
def fix_vars(_vars, reverse = False):
    for var in _vars:
        if not(reverse):
            var.fix()
        else:
            var.unfix()
    return 



def add_cuids_to_list(varname, iterator, lista, timeindex = '*'):
    def index_to_string(index):
        if type(index) in [tuple, list]:
            index_str = ''
            for cc in index:
                index_str += f'{cc},'
        elif type(index) == str:
            index_str = f'{index},'
        return index_str
    for index in iterator:
        index_str = index_to_string(index)
        cuid = f'{varname}[{index_str}{timeindex}]'
        lista.append(cuid) 
    return lista

def cuids_at_t0(names, t0):
    new_names = [name.replace('*]', f'{str(t0)}]') for name in names]
    return new_names

# TIME LINKER
def build_time_linker(times_load, times_get = []):
    ''' 
    Build a time linker (dictionary) between 
    timestep to load (plant) and timestep from which data is got (controller)
    '''
    if times_get == []:
        times_get = times_load
    assert(len(times_get) == len(times_load)), 'Time linker non funziona adesso!'
    # corrispondenza 1 a 1
    if len(times_get) == len(times_load):
        t_linker = {
            list(times_load)[i] : list(times_get)[i]
            for i in range(0, len(times_load))}
    return t_linker


def load_data_series_helper(helper, data, times_load, times_get = []):
    ''' 
    Load data series into a model using nmpc helper
    '''
    # load data series into model by means of helper 
    t_linker = build_time_linker(times_load, times_get)
    for tl in t_linker.keys():
        tg = t_linker[tl]
        load_data = data.get_data_at_time(tg) 
        helper.load_data_at_time(load_data, time_points = tl)
    return 


def steady_init_options(Options):
    ''' 
    Set up options for first state initialization
    '''
    Options_steady = copy.deepcopy(Options)
    Options_steady['T'] = Options['T0']
    Options_steady['steady'] = True
    return Options_steady



######################## GASNETWORK MODEL #####################################
###############################################################################

def make_gasnetwork_model(
        DataContainer, Options):
    
    ''' 
    Make gasnetwork model
    '''

    # Unwrap container
    networkData = DataContainer["networkData"]
    stationData = DataContainer["stationData"]
    inputData = DataContainer["inputData"]
    scale = DataContainer["scale"]
    
    # ! replace with gasnetwork model
    m = buildNonLinearModel(
                networkData, stationData, inputData, Options, scale)

    return m



######################## NMPC DATA EXCHANGE ###################################
###############################################################################

def nmpc_gasnetwork_data_exchange(
        DataContainer, Options):
    ''' 
    Define data exchanged between nmpc entities (plant/controller)

    INPUT:
        - DataContainer --> dictionary with Station, inputData, networkData information
    
    OUTPUT:
        (lists of string cuids)
        - control_inputs --> controller actions on the plant (from CONTROLLER to PLANT, compressors N*, cv_teta)
        - initial_conditions --> model initial conditions (from PLANT to CONTROLLER, derivative variables, interm_p)
        - exogenous_inputs --> exogenous data to the model (shifted in controller, from CONTROLLER to PLANT)
    '''
    # ! remove unit commitment and control valves
    # 
    # Unit commtiment
    unit_commitment = ['yJ[*,*,*,*]']
    
    # Exogenous inputs
    exogenous_inputs = ['wCons[*,*,*]', 'wSource[*,*]','pSource[*,*]', 'pCV[*,*]']

    #
    # Initial conditions --> interm_p (derivative variable)
    # build iterator
    networkData = DataContainer['networkData']
    Pipes_Vol = [] # to define interm  pressure
    for p in networkData["Pipes"].keys():
        N = networkData["Pipes"][p]["Nvol"]
        for vol in range(2,N+1):
            Pipes_Vol.append((p,vol))   
    # update nmpc data container        
    initial_conditions = add_cuids_to_list(
        'interm_p', Pipes_Vol, [], timeindex = Options['T0'])
    
    # Control inputs
    control_inputs = ['NStar[*,*,*]', 'cv_teta[*,*]']


    return control_inputs, initial_conditions, exogenous_inputs, unit_commitment




######################## NMPC GAS NETWORK #####################################
###############################################################################

def run_economic_nmpc(
        DataContainer, Options, plant_horizon, 
        ):

    

    #==========================================================================
    ### DEFINE DATA EXCHANGE between entities
    control_inputs, initial_conditions, exogenous_inputs, unit_commitment = nmpc_gasnetwork_data_exchange(
        DataContainer, Options)
    
    #==========================================================================
    ### SOLVER ###
    ipopt = pyo.SolverFactory("ipopt")
    
    #==========================================================================
    print('** Retrieving starting solution (steady-state) **')
    ### INITIALIZATION (first state model) ###
    #
    # Build plant model (steady) (used for initial condition of both plant and controller)
    Options_steady = steady_init_options(Options)
    m_steady = make_gasnetwork_model(
            DataContainer, Options_steady)
    
    #
    # Call steady nmpc helpers (tools to retrieve data)
    # helper on set: time
    m_steady_helper = DynamicModelHelper(m_steady, m_steady.Times)
    
    # 
    # Solve and get data
    res_s = ipopt.solve(m_steady, tee=True)
    pyo.assert_optimal_termination(res_s)
    t0 = m_steady.Times.first()
    steady_initial_data = m_steady_helper.get_data_at_time(t0, include_expr=True)
            
    #==========================================================================
    ### PLANT MODEL (simulation) ### 
    print('** Building plant model **')
    #
    # Build plant model (dynamic)
    m_plant = make_gasnetwork_model(DataContainer, Options)
    
    #
    # Define timeframes
    # General
    time_p = m_plant.Times
    t0 = m_plant.Times.first()
    tf_p = m_plant.Times.last()
    # Define controller inputs timeframe into plant (all times except the first one)
    non_initial_plant_time = list(time_p)[1:]
    
    #
    # Call plant nmpc helpers 
    # helper set: time
    m_plant_helper = DynamicModelHelper(m_plant, time_p)

    
    #
    # Fix variables
    # Initial conditions (derivative vars)
    plant_init_vars = [m_plant.find_component(name) for name in initial_conditions]
    fix_vars(plant_init_vars)
    
    # Inputs in plant (N*,unit commitment, cv opening)
    plant_input_vars = [m_plant.find_component(name) for name in control_inputs]
    fix_vars(plant_input_vars)
    
    #
    # Initialize containers (store plant actions for postptocessing)
    plant_data_list = m_plant_helper.get_data_at_time([t0])
    objective_list = []
    
    #==========================================================================
    ### CONTROLLER (optimization) ###
    print('** Building controller model **')
    #
    # Build model
    m_controller = make_gasnetwork_model(DataContainer, Options)
    
    #
    # Define timeframes
    time_c = m_controller.Times
    non_initial_controller_time = list(time_c)[1:]
    
    #
    # Call nmpc helpers (used to access data)
    m_controller_helper = DynamicModelHelper(m_controller, time_c)    
    
    # Steady state variables (t0)
    m_controller_helper.load_data_at_time(steady_initial_data, t0)
    
    #
    # Fix 
    # Initial conditions (derivative vars)
    controller_init_vars = [m_controller.find_component(name) for name in initial_conditions]
    fix_vars(controller_init_vars)
    
    # Initial control setting (N* and unit commiment), from first state
    control_inputs_t0 =  cuids_at_t0(control_inputs, t0) 
    controller_input_vars_t0 = [m_controller.find_component(name) for name in control_inputs_t0]
    controller_uc_vars_t0 = [m_controller.find_component(name.replace('*]', f'{str(t0)}]')) for name in unit_commitment]
    fix_vars(controller_input_vars_t0 + controller_uc_vars_t0)
    
    #
    # Initialize containers (store controller's predictions for postprocessing)
    controller_data_list = m_controller_helper.get_data_at_time([t0])
       
    #==========================================================================
    
    # Define rolling horizon
    controller_horizon = (time_c[-1] - t0)
    n_cycles = round(controller_horizon/plant_horizon)

    controller_iters_data = []
    controller_iters_uc_data = []
    time_list = []
    #==========================================================================
    # CYCLES
    print('** Starting rolling horizon **')
    for i in range(0, n_cycles):
        print(f'xxx Iter {i} xxx')
            
        # simulation framework (shift time data)
        sim_t0 = i * (plant_horizon)
        
        #======================================================================
        ### CONTROLLER  ###
        
        res = ipopt.solve(m_controller, tee=True)
        time_list.append(res.Solver.Time)
        # 
        # Get data (non_initial_plant_time_uc)
        # Controller 
        controller_data = m_controller_helper.get_data_at_time(non_initial_plant_time)

        #======================================================================
        ### PLANT ###

        # Load initial state from controller at first iteration --> steady state solution (could have been uploaded before)
        if i == 0:
            controller_data_t0 = m_controller_helper.get_data_at_time([t0])
            load_data_series_helper(m_plant_helper, controller_data_t0, [t0]) 
    
        # Controller inputs + exogenous variables 
        load_data_series_helper(
            m_plant_helper, controller_data, non_initial_plant_time)            

        res_p = ipopt.solve(m_plant, tee=True)
        
    
        #
        # Store data
        plant_data = m_plant_helper.get_data_at_time(non_initial_plant_time, include_expr=True)# Load plant data 
        plant_data.shift_time_points(sim_t0) # Shift time points
        plant_data_list.concatenate(plant_data) # Update container
        
        #
        # Store objective
        objective_list.append(pyo.value(m_plant.ObjFun))
        

        # Update containers
        controller_data.shift_time_points(sim_t0) # Shift time points from "controller time" to "simulation time" (sim_t0)
        controller_data_list.concatenate(controller_data) 
        # debug- containers
        controller_iters_data.append(m_controller_helper.get_data_at_time(time_c))
    
        #======================================================================
    
        # Shift all variables in controller
        print('...Shifting variables')
        # ! I modified the nmpc function with cyclic=True (used for exogenous inputs, e.g. gas network demand)
        m_controller_helper.shift_values_by_time(plant_horizon, cyclic=True) # it needs a dynamic time set

        
        #======================================================================
        ## RE-INITIALIZATION (with plant final state)
        
        #
        # Load plant's current state and re-initialize both controller and plant.
        # Remark: This sets all initial conditions, including exogenous variables!
        
        # Continuous data
        plant_current_data = m_plant_helper.get_data_at_time(tf_p)
        m_controller_helper.load_data_at_time(plant_current_data, time_points = t0)# Re-initialize controller
        m_plant_helper.load_data_at_time(plant_current_data, time_points = t0)# Re-initialize plant 
     
    return controller_data_list, plant_data_list

