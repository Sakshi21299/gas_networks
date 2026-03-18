# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 18:17:24 2024

@author: ssnaik
"""
#Calculate cyclic steady state for 72 hour horizon with periodic constraints 
#i.e. z(N-1)K = z(NK)

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
from gas_net.modelling_library.terminal import css_terminal_constraints

input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData_longer_horizon.xlsx'

cycle_length = 12
m_steady, m_dyn = run_model(horizon = cycle_length, num_time_periods = 1, input_data_path = input_data_path, 
                            periodic_constraints = False, calculating_css=True, 
                            uncertainty= None) 
m_dyn_interface = mpc.DynamicModelInterface(m_dyn, m_dyn.Times)
sim_data = m_dyn_interface.get_data_at_time(list(m_dyn.Times))

#All pressure variables at demand nodes
all_nodes_p = []
for n in m_dyn.Nodes:
    if str(n).startswith('sink'):
        all_nodes_p.append(m_dyn.node_p[n, :])
from gas_net.util.write_data_to_excel import write_data_to_excel
sheets_keys_dict = {"compressor power": [m_dyn.compressor_P[s, :] for s in m_dyn.Stations], 
                    "compressor beta": [m_dyn.compressor_beta[s, :] for s in m_dyn.Stations], 
                    "wCons": [m_dyn.wCons[s, 0, :] for s in m_dyn.Nodes if str(s).startswith('sink')], 
                    "node pressure": all_nodes_p, 
                    "interm_w": [m_dyn.interm_w[p, vol, :] for p, vol in m_dyn.Pipes_VolExtrC_interm],
                    "interm_p": [m_dyn.interm_p[p, vol, :] for p, vol in m_dyn.Pipes_VolExtrR_interm],
                    "wSource": [m_dyn.wSource[s, :] for s in m_dyn.NodesSources],
                    "pSource": [m_dyn.pSource[s, :] for s in m_dyn.NodesSources],
                    "pipe_rho": [m_dyn.pipe_rho[p, vol, :] for p, vol in m_dyn.Pipes_VolExtrR]
                    }
write_data_to_excel(sim_data, m_dyn, sheets_keys_dict, "optimal_css_12hrs_gaslib40_infhorizon_small_demand.xlsx")


#Plot
plot_compressor_beta(m_dyn)
plot_compressor_power(m_dyn)

import numpy as np
import matplotlib.pyplot as plt
speed = {}
for p in m_dyn.Pipes:
    speed[p] = []
    for t in m_dyn.Times:
        sum_u_at_t = 0
        for v in m_dyn.Pipes_VolExtrC:
            sum_u_at_t += abs(pyo.value(m_dyn.u[p, v[1], t]))
        avg_speed_at_t = sum_u_at_t/len(m_dyn.Pipes_VolExtrC)
        speed[p].append(avg_speed_at_t)
plt.figure()
for key in speed.keys():
    plt.plot(speed[key], label = key)
plt.legend()

#Check if states are the same
import math 
for p, v in m_dyn.Pipes_VolExtrC_interm:
    try:
        assert math.isclose(pyo.value(m_dyn.interm_w[p, v, 0]), pyo.value(m_dyn.interm_w[p, v, cycle_length]))
    except:
        print(pyo.value(m_dyn.interm_w[p, v, 0]), pyo.value(m_dyn.interm_w[p, v, cycle_length]))
for s in m_dyn.Nodes:
    assert math.isclose(pyo.value(m_dyn.node_p[s, 0]), pyo.value(m_dyn.node_p[s, cycle_length]))
    
for s in m_dyn.NodesSources:
    assert math.isclose(pyo.value(m_dyn.wSource[s, 0]), pyo.value(m_dyn.wSource[s, cycle_length]))
    