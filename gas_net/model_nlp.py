# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 10:49:55 2021

@author: Lavinia
"""

import pyomo.environ as pyo

# components (parameters)
from gas_net.modelling_library.PARAMS import (
    PIPE_gas_params, PIPE_geom_params, PIPE_smoothing_params)

# componrts (sets)
from gas_net.modelling_library.SETS import (
    TIME_sets, NODE_sets, ARC_sets, STATION_set, PIPE_sets, VALVE_sets)

# components (vars)
from gas_net.modelling_library.VARS import (
    NODE_vars, ARC_vars, STATIONS_vars,
    PIPE_vars, DUALS_ipopt_vars)           

# from modelling_library.BOUNDSVAR import set_extra_bounds                                    


# components (fix inputs)
from gas_net.modelling_library.fix_and_init_vars import fix_exogenous_inputs

# components (constraints)
from gas_net.modelling_library.objective_functions import OBJ_compressor_power
from gas_net.modelling_library.nodes import NODE_constr, NODE_SOURCE_constr
from gas_net.modelling_library.stations import STATION_constr
from gas_net.modelling_library.pipes.constraints import (
    PIPE_mass_constr, PIPE_momentum_constr, PIPE_nlp_auxiliary_constr, PIPE_flow_reversal_constr)
from gas_net.modelling_library.valves import VALVE_constr
                                                       
#==============================================================================
""" BUILD MODEL """
#==============================================================================

def buildNonLinearModel(
        networkData, inputData, Opt, duals=False):
    
    # scale dictionary --> scales variables (variables are all defined in SI base units)
    scale = {
        "p": 100000, # pressure
        "P": 100000, # compressor power
        "w": 1, # mass flow
        'u2': 10 # squared speed
        }

    # MODEL
    m = pyo.ConcreteModel("gasnetwork")
    
    ############################### SETS ####################################
    ###########################################################################
    
    # TIME
    m = TIME_sets(m, Opt)
    # NETWORK
    m = NODE_sets(m, networkData)
    m = ARC_sets(m, networkData)
    # STATION
    m = STATION_set(m, networkData)
    # PIPES
    m = PIPE_sets(m, networkData)
    # VALVES
    m = VALVE_sets(m, networkData)
    
    ############################### PARAMS ####################################
    ###########################################################################
        
    # GAS parameters
    m = PIPE_gas_params(m, networkData)
    # Geometry
    m = PIPE_geom_params(m, networkData)
    # Smoothing
    m = PIPE_smoothing_params(m, Opt['eps'])

    ############################### VARIABLES #################################
    ###########################################################################

    # NETWORK
    m = NODE_vars(m)
    m = ARC_vars(m)
    # STATION
    m = STATIONS_vars(m)
    # PIPES
    m = PIPE_vars(m, scale, networkData)
    # DUALS
    if duals:
        m = DUALS_ipopt_vars(m)             
    # FIX EXOGENOUS INPUTS (TIME varying input variables)
    # ! FIX EXOGENOUS INPUTS ONCE DATA IS AVAILABLE
    m = fix_exogenous_inputs(m, scale, Opt, networkData, inputData)

    ############################### OBJECTIVE FUNCTION ########################
    ###########################################################################
    
    m = OBJ_compressor_power(m, Opt)

    ############################### CONSTRAINTS ###############################
    ###########################################################################

    # NODES
    m = NODE_constr(m, scale, networkData)
    m = NODE_SOURCE_constr(m) # supply nodes
    # STATION
    m = STATION_constr(m, scale, inputData)
    # VALVE
    m = VALVE_constr(m)
    # PIPE
    m = PIPE_mass_constr(
            m, scale, Opt['dt'], 
            method = Opt["finite_diff_time"], dynamic = Opt['dynamic'])
    m = PIPE_momentum_constr(m, scale, networkData)
    m = PIPE_nlp_auxiliary_constr( m, scale)
    m = PIPE_flow_reversal_constr(m, scale)  # flow reversal         
    
    if Opt["finite_diff_time"] == 'COLLOCATION' and Opt['dynamic']:
        discretizer = pyo.TransformationFactory('dae.collocation')
        discretizer.apply_to(m, wrt=m.Times, nfe=Opt["nfe"], ncp=Opt["ncp"], scheme='LAGRANGE-RADAU')
        
        m = discretizer.reduce_collocation_points(m,
                                                   var=m.compressor_P,
                                                   ncp=1,
                                                   contset=m.Times)
        
    return m