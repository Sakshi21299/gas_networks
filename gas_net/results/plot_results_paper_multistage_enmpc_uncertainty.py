# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 11:38:04 2025

@author: ssnaik
"""

import matplotlib.pyplot as plt
import matplotlib.patches as pt
import pandas as pd
import os
import numpy as np
TRANSPARENT = True
FONTSIZE = 16
AXESOFF = True
LINEWIDTH = 4.0

plt.rcParams["font.size"] = FONTSIZE
plt.rcParams["text.usetex"] = True
plt.rcParams["font.family"] = 'serif'

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\final_results\final_paper_results\kai_unc_demands_only\unsteady_start"

file_name = r"enmpc_multistage_kai_72hrs_random_scenario_l1_slack.xlsx"
file_path = os.path.join(path, file_name)
df_multistage = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

savefig_path = r"C:\Users\ssnaik"

#Plot demand at sink nodes
fig, ax = plt.subplots()
ax.plot(df_multistage['wCons'][:], 'salmon')
ax.plot(df_multistage['wCons'][df_multistage['wCons'].columns[1]], 'salmon', label = '$\mathrm{Demand \: achieved}$')
#ax.plot(df_multistage['wCons_target'][:], ':k', label = '$\mathrm{Target \: demand}$')
ax.set_ylabel("$\mathrm{Flow (kg/s)}$")
ax.set_xlabel('$\mathrm{Time(hrs)}$')
ax.legend()
fig.tight_layout()
#fig.savefig(os.path.join(savefig_path, "flow_at_sink_nodes_unc_multistage_enmpc.pdf"))

#Plot compressor beta
plt.figure()
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]'], color = 'salmon', label = '$\mathrm{C} 1$')
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_2'" + ', :]'], color = 'b', label = '$\mathrm{C} 2$')
plt.plot(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_3'" + ', :]'], color = 'brown', label = '$\mathrm{C} 3$')
#plt.ylim(1, 1.9)
plt.ylabel("$\mathrm{Compressor }$" + r"$\beta$")
plt.xlabel('$\mathrm{Time(hrs)}$')
#plt.title("Compressor controls - Standard ENMPC")
plt.legend(bbox_to_anchor=(0.96, 0.45), loc = 'lower right', fontsize = 12)
plt.tight_layout()
#plt.savefig(os.path.join(savefig_path,"compressor_beta_unc_multistage_enmpc.pdf"))

#Plot lyapunov function
plt.figure()
plt.plot(1/3*(df_multistage['controller_lyapunov']['controller_1_lyapunov'] + 
         df_multistage['controller_lyapunov']['controller_2_lyapunov'] +
         df_multistage['controller_lyapunov']['controller_3_lyapunov']))
plt.ylabel("Avg Lyapunov value function")
plt.xlabel("Time (hrs)")
plt.tight_layout()
#plt.ylim(0, 50)
plt.savefig(os.path.join(savefig_path, "kai-lyapunov_value_function_multistage_enmpc_l1_slack.pdf"))


#Compare enmpc and multistage total power 
# file_name = r"final_paper_kai_enmpc_periodic_with_stability_72hrs_random_uncertain_demands_seed42.xlsx"
# file_path = os.path.join(path, file_name)
# df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

# fig, ax = plt.subplots()
# ax.plot(df_multistage['compressor power'].sum(axis = 1)*10**3, color = 'deeppink', label = 'Multistage')
# ax.plot(df_standard['compressor power'].sum(axis = 1)*10**3, ':',color = 'k', label = 'Standard')
# ax.legend()
# ax.set_ylabel("Power (MWh)")
# ax.set_xlabel("Time (hrs)")
# fig.tight_layout()
#fig.savefig(os.path.join(savefig_path, "power_comparison_multistage_vs_std_enmpc.pdf"))

#Plot sink pressures
plt.figure()
x = np.linspace(41, 41, len(df_multistage['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]']))
plt.plot(x, '--k')
plt.plot(df_multistage['node pressure']['node_p[' + "'sink_1'" + ', :]'], label = 'Sink 1')
plt.plot(df_multistage['node pressure']['node_p[' + "'sink_2'" + ', :]'], label = 'Sink 2')
plt.plot(df_multistage['node pressure']['node_p[' + "'sink_3'" + ', :]'], label = 'Sink 3')
plt.plot(df_multistage['node pressure']['node_p[' + "'sink_4'" + ', :]'], label = 'Sink 4')
plt.plot(df_multistage['node pressure']['node_p[' + "'sink_5'" + ', :]'], label = 'Sink 5')

plt.legend()
plt.ylabel("Pressure (bar)")
plt.xlabel('$\mathrm{Time(hrs)}$')

fig , ax = plt.subplots(1,5, figsize = (20, 4))
ax[0].plot(df_multistage['node pressure']['node_p[' + "'sink_1'" + ', :]'], 'r', label = 'Sink 1')
ax[1].plot(df_multistage['node pressure']['node_p[' + "'sink_2'" + ', :]'], 'b',label = 'Sink 2')
ax[2].plot(df_multistage['node pressure']['node_p[' + "'sink_3'" + ', :]'], 'g',label = 'Sink 3')
ax[3].plot(df_multistage['node pressure']['node_p[' + "'sink_4'" + ', :]'], 'magenta',label = 'Sink 4')
ax[4].plot(df_multistage['node pressure']['node_p[' + "'sink_5'" + ', :]'], 'darkorange',label = 'Sink 5')
for i in range(5):
    ax[i].plot(x, '--k')
    ax[i].set_title('Sink %i'%(i+1), fontsize = 24)
    ax[i].set_ylim(40.4, 43)
    ax[i].set_xlabel("Time (hrs)", fontsize = 24)
ax[0].set_ylabel("Pressure (bar)", fontsize = 24)
plt.tight_layout()
plt.savefig(os.path.join(savefig_path, "kai_sink_pressures_multistage_unc_l1_slack.pdf"))

plt.figure()
plt.plot(df_multistage['node pressure']['node_p[' + "'sink_1'" + ', :]'], 'r', label = 'Sink 1')
plt.plot(x, '--k')
plt.xlabel('Time(hrs)')
plt.ylabel('Pressure(bar)')
plt.ylim(40.5, 43)
plt.tight_layout()
plt.savefig('kai_pressure_sink_1_multistage.png', dpi = 300)
