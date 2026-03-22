# -*- coding: utf-8 -*-
"""
Created on Sun Oct  6 11:44:29 2024

@author: ssnaik
"""
#PLottin multistage results

import matplotlib.pyplot as plt
import pandas as pd
import os

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results"

file_name = r"final_results\enmpc_experiments\enmpc_multistage_gaslib40_72hrs_random_scenario_explicit_terminal_constraints_avg_stability.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = r"final_results\enmpc_experiments\enmpc_multistage_gaslib40_72hrs_random_scenario.xlsx"
file_path = os.path.join(path, file_name)
df_standard_enmpc = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = "optimal_css_24hrs_max_scenario_extended.xlsx"
file_path = os.path.join(path, file_name)
df_optimal_css_max = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")
file_name = "optimal_css_24hrs_min_scenario_extended.xlsx"
file_path = os.path.join(path, file_name)
df_optimal_css_min = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")
file_name = "optimal_css_24hrs_extended.xlsx"
file_path = os.path.join(path, file_name)
df_optimal_css_nom = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

savefig_path = r"C:\Users\ssnaik" #"\Biegler\gas_networks_italy\gas_networks\gas_net\results\plots\multistage_tracking_nmpc"
#Plot demand at sink nodes

plt.figure()

plt.plot(df_standard_enmpc['wCons'][:], 'salmon')
plt.plot(df_standard['wCons']["wCons['sink_4', 0, :]"], ':k', label = 'Target demand')
# plt.plot(df_optimal_css_max['wCons']["wCons['sink_4', 0, :]"], ':k', label = 'Max scenario')
# plt.plot(df_optimal_css_nom['wCons']["wCons['sink_4', 0, :]"], ':b', label = 'Nom scenario')
# plt.plot(df_optimal_css_min['wCons']["wCons['sink_4', 0, :]"], ':r', label = 'Min scenario')

plt.ylabel("Flow (kg/s)")
plt.xlabel('Time(hrs)')
plt.title("Flow at sink nodes in the plant - Standard E-NMPC")
plt.ylim(15.4, 17.3)
plt.legend()
plt.savefig(os.path.join(savefig_path, "flow_at_sink_nodes_enmpc_random_scenario.svg"))

#Plot node pressures
plt.figure()
plt.plot(df_standard['node pressure'][:])
plt.ylabel("Pressure at sink nodes")
plt.xlabel('Time(hrs)')
plt.title("Pressure at sink nodes in the plant - Multistage tracking NMPC")
plt.savefig(os.path.join(savefig_path,"pressure_at_sink_nodes.png"), dpi = 300)

#Plot source flows
plt.figure()
plt.plot(df_standard['wSource'][:])
plt.ylabel("Flow at source nodes")
plt.xlabel('Time(hrs)')
plt.title("Flow at source nodes in the plant - Multistage tracking NMPC")
plt.savefig(os.path.join(savefig_path,"flow_at_source_nodes.png"), dpi = 300)

#Plot source pressures
plt.figure()
plt.plot(df_standard['pSource'][:])
plt.ylim(54, 59)
plt.ylabel("Pressure at source nodes")
plt.xlabel('Time(hrs)')
plt.title("Pressure at source nodes in the plant - Multistage tracking NMPC")
plt.savefig(os.path.join(savefig_path,"pressure_at_source_nodes.png"), dpi = 300)


#Plot intermediate pressures 
plt.figure()
plt.plot(df_standard['interm_p'][:])
plt.ylabel("Intermediate pressures in pipes")
plt.xlabel('Time(hrs)')
plt.title("Intermediate pressure in pipes in plant - Multistage tracking NMPC")

#Plot intermediate flows 
plt.figure()
plt.plot(df_standard['interm_w'][:])
plt.ylabel("Intermediate flows in pipes")
plt.xlabel('Time(hrs)')
plt.title("Intermediate flows in pipes in plant - Multistage tracking NMPC")

#Plot controls
plt.figure()
plt.plot(df_standard['compressor beta'][:])
plt.ylabel("Compressor beta")
plt.xlabel('Time(hrs)')
plt.title("Compressor controls - Multistage tracking NMPC")
plt.savefig(os.path.join(savefig_path,"compressor_beta.png"), dpi = 300)

#Plot compressor power
plt.figure()
plt.plot(df_standard['compressor power'].sum(axis = 1)*10**5, 'salmon', label = 'Multistage E-NMPC restrictive modified')
plt.plot(df_standard_enmpc['compressor power'].sum(axis = 1)*10**5, ':k', label = 'Multistage E-NMPC loose')
plt.ylabel("Power (kWh)")
plt.xlabel('Time(hrs)')
plt.title("Total compressor power")
plt.legend()
plt.savefig(os.path.join(savefig_path,"compressor_power.svg"))

#Plot lyapunov value function
plt.figure()
plt.plot(1/3*(df_standard['controller_lyapunov']['controller_1_lyapunov'] + 
         df_standard['controller_lyapunov']['controller_2_lyapunov'] +
         df_standard['controller_lyapunov']['controller_3_lyapunov']))
plt.xlabel("Time (hrs)")
plt.ylabel("Expected Lyapunov value function")
plt.savefig(os.path.join(savefig_path, "Expected_lyapunov_value_function.svg"))