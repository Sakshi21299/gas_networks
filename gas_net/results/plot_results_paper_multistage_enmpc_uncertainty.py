# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 11:38:04 2025

@author: ssnaik
"""

import matplotlib.pyplot as plt
import matplotlib.patches as pt
import pandas as pd
import os
TRANSPARENT = True
FONTSIZE = 16
AXESOFF = True
LINEWIDTH = 4.0

plt.rcParams["font.size"] = FONTSIZE
plt.rcParams["text.usetex"] = True
plt.rcParams["font.family"] = 'serif'

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\final_results"

file_name = r"final_paper_results\final_paper_enmpc_multistage_random_scenario_explicit_terminal_constraints_avg_stability.xlsx"
file_path = os.path.join(path, file_name)
df_multistage = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

savefig_path = r"C:\Users\ssnaik"

#Plot demand at sink nodes
fig, ax = plt.subplots()
ax.plot(df_multistage['wCons'][:], 'salmon')
ax.plot(df_multistage['wCons'][df_multistage['wCons'].columns[1]], 'salmon', label = '$\mathrm{Demand \: achieved}$')
ax.plot(df_multistage['wCons_target'][:], ':k', label = '$\mathrm{Target \: demand}$')
ax.set_ylabel("$\mathrm{Flow (kg/s)}$")
ax.set_xlabel('$\mathrm{Time(hrs)}$')
ax.set_ylim(15.4, 17.3)
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(savefig_path, "flow_at_sink_nodes_unc_multistage_enmpc.pdf"))

#Plot compressor beta
plt.figure()
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]'], color = 'salmon', label = '$\mathrm{C} 1$')
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_2'" + ', :]'], color = 'b', label = '$\mathrm{C} 2$')
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_3'" + ', :]'], color = 'brown', label = '$\mathrm{C} 3$')
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_4'" + ', :]'], color = 'y', label = '$\mathrm{C} 4$')
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_5'" + ', :]'], color = 'r', label = '$\mathrm{C} 5$')
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_6'" + ', :]'], color = 'g', label = '$\mathrm{C} 6$')
#plt.ylim(1, 1.9)
plt.ylabel("$\mathrm{Compressor }$" + r" $\beta $")
plt.xlabel('$\mathrm{Time(hrs)}$')
#plt.title("Compressor controls - Standard ENMPC")
plt.legend(bbox_to_anchor=(0.96, 0.45), loc = 'lower right', fontsize = 12)
plt.tight_layout()
plt.savefig(os.path.join(savefig_path,"compressor_beta_unc_multistage_enmpc.pdf"))

#Plot lyapunov function
plt.figure()
plt.plot(1/3*(df_multistage['controller_lyapunov']['controller_1_lyapunov'] + 
         df_multistage['controller_lyapunov']['controller_2_lyapunov'] +
         df_multistage['controller_lyapunov']['controller_3_lyapunov']))
plt.ylabel("Avg Lyapunov value function")
plt.xlabel("Time (hrs)")
plt.tight_layout()
plt.savefig(os.path.join(savefig_path, "lyapunov_value_function_multistage_enmpc.pdf"))

fig, ax = plt.subplots()
ax.plot(1/3*(df_multistage['controller_lyapunov']['controller_1_lyapunov'] + 
          df_multistage['controller_lyapunov']['controller_2_lyapunov'] +
          df_multistage['controller_lyapunov']['controller_3_lyapunov']))
ax.set_ylabel("Avg Lyapunov value function")
ax.set_xlabel("Time (hrs)")
plt.xlim(10, 73)
plt.ylim(0, 200)
fig.tight_layout()
fig.savefig(os.path.join(savefig_path, "lyapunov_value_function_multistage_enmpc_zoom.pdf"))

#Compare enmpc and multistage total power 
file_name = r"final_paper_results\final_paper_enmpc_periodic_without_stability_72hrs_random_uncertain_demands.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

fig, ax = plt.subplots()
ax.plot(df_multistage['compressor power'].sum(axis = 1)*10**3, color = 'deeppink', label = 'Multistage')
ax.plot(df_standard['compressor power'].sum(axis = 1)*10**3, ':',color = 'k', label = 'Standard')
ax.legend()
ax.set_ylabel("Energy (MWh)")
ax.set_xlabel("Time (hrs)")
square1 = pt.Rectangle((45, 345), 10, 200, linewidth=1, edgecolor='k', facecolor='none')
#ax.add_patch(square1)
fig.tight_layout()
fig.savefig(os.path.join(savefig_path, "power_comparison_multistage_vs_std_enmpc.pdf"))

fig, ax = plt.subplots()
ax.plot(df_multistage['wSource']['wSource[' + "'source_1'" + ', :]'], 'b', label = 'Multistage')
ax.plot(df_standard['wSource']['wSource[' + "'source_1'" + ', :]'], ':k', label = 'Standard')
ax.set_ylabel("$\mathrm{Flow (kg/s)}$")
ax.set_xlabel('$\mathrm{Time(hrs)}$')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(savefig_path, "source1_flow_multistage_vs_std_enmpc.pdf"))

fig, ax = plt.subplots()
ax.plot(df_multistage['wSource']['wSource[' + "'source_2'" + ', :]'], 'g', label = 'Multistage')
ax.plot(df_standard['wSource']['wSource[' + "'source_2'" + ', :]'], ':k', label = 'Standard')
ax.set_ylabel("$\mathrm{Flow (kg/s)}$")
ax.set_xlabel('$\mathrm{Time(hrs)}$')
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(savefig_path, "source2_flow_multistage_vs_std_enmpc.pdf"))




