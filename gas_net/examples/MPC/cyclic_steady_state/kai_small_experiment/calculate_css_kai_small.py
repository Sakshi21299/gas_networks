# -*- coding: utf-8 -*-
"""
Created on Sun Jan 26 14:32:42 2025

@author: ssnaik
"""

#Calculate cyclic steady state for 72 hour horizon with periodic constraints 
#i.e. z(N-1)K = z(NK)

import pyomo.contrib.mpc as mpc
import pyomo.environ as pyo
from gas_net.examples.run_nlp_kai_small import run_model
from gas_net.util.plotting_util.plot_dynamic_profiles import *

input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\kai_small\\inputData_longer_horizon.xlsx'
m_steady, m_dyn = run_model(horizon = 6, num_time_periods = 1, input_data_path = input_data_path, 
                            periodic_constraints = False, calculating_css=True, 
                           ) 
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
                    "node pressure": [m_dyn.node_p[n, :] for n in m_dyn.Nodes if str(n).startswith('sink')], 
                    "interm_w": [m_dyn.interm_w[p, vol, :] for p, vol in m_dyn.Pipes_VolExtrC_interm],
                    "interm_p": [m_dyn.interm_p[p, vol, :] for p, vol in m_dyn.Pipes_VolExtrR_interm],
                    "wSource": [m_dyn.wSource[s, :] for s in m_dyn.NodesSources],
                    "pSource": [m_dyn.pSource[s, :] for s in m_dyn.NodesSources]
                    }
write_data_to_excel(sim_data, m_dyn, sheets_keys_dict, "optimal_css_24hrs_inf_horizon.xlsx")


#Plot
plot_compressor_beta(m_dyn)
plot_compressor_power(m_dyn)
plot_sink_flow(m_dyn)
plot_pressures(m_dyn)
#Check if states are the same
import math 
for p, v in m_dyn.Pipes_VolExtrC_interm:
    assert math.isclose(pyo.value(m_dyn.interm_w[p, v, 0]), pyo.value(m_dyn.interm_w[p, v, 6]))
    
for s in m_dyn.Nodes:
    assert math.isclose(pyo.value(m_dyn.node_p[s, 0]), pyo.value(m_dyn.node_p[s,6]))
    
for s in m_dyn.NodesSources:
    assert math.isclose(pyo.value(m_dyn.wSource[s, 0]), pyo.value(m_dyn.wSource[s, 6]))
    