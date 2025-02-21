# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 08:54:55 2024

@author: ssnaik
"""
import matplotlib.pyplot as plt
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

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net"

file_name = r"results\final_results\final_paper_results\kai_unc_demands_only\unsteady_start\final_paper_kai_enmpc_explicit_terminal_each_point_stability_72hrs.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = r"optimal_css_24hrs_kai.xlsx"
file_path = os.path.join(path, file_name)
df_optimal_css = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

savefig_path = r"C:\Users\ssnaik"#\Biegler\gas_networks_italy\gas_networks\gas_net\results\plots\economic_nmpc_experiments\standard_enmpc"
#Plot demand at sink nodes
plt.figure()
plt.plot(df_standard['wCons'][:], 'salmon')
plt.plot(df_standard['wCons'][df_standard['wCons'].columns[1]], 'salmon', label = '$\mathrm{Demand \: achieved}$')
plt.plot(df_optimal_css['wCons'][df_optimal_css['wCons'].columns[1]], ':k', label = '$\mathrm{Target \: demand}$')
plt.ylabel("$\mathrm{Flow (kg/s)}$")
plt.xlabel('$\mathrm{Time(hrs)}$')
#plt.title("$\mathrm{Flow at sink nodes in the plant - Standard E-NMPC}")
#plt.ylim(15.4, 17.3)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(savefig_path, "kai_flow_at_sink_nodes_no_unc_std_enmpc.pdf"))

#Plot controls
plt.figure()
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]'], color = 'salmon', label = '$\mathrm{C} 1$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_2'" + ', :]'], color = 'b', label = '$\mathrm{C} 2$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_3'" + ', :]'], color = 'brown', label = '$\mathrm{C} 3$')
plt.ylabel("$\mathrm{Compressor }$" + r" $\beta $")
plt.xlabel('$\mathrm{Time(hrs)}$')
plt.legend(fontsize = 12)
plt.tight_layout()
plt.savefig(os.path.join(savefig_path,"kai_compressor_beta_no_unc_std_enmpc.pdf"))


#Plot source flow css
fig , ax = plt.subplots(1,1)
ax.plot(df_optimal_css['wSource']['wSource[' + "'source_1'" + ', :]'], ':', color='k', label = 'Optimal CSS')
ax.plot(df_standard['wSource']['wSource[' + "'source_1'" + ', :]'], '--b')
ax.set_ylabel("$\mathrm{Flow (kg/s)}$", fontsize = 20)
ax.set_xlabel('$\mathrm{Time(hrs)}$', fontsize = 20)
ax.set_title('Source 1 (S1)')

ax.axvline(x=48, color='orange', linestyle='-') 

fig.tight_layout()
#plt.savefig(os.path.join(savefig_path,"ocss_supply.pdf"))



#Plot lyapunov value function
plt.figure()
plt.plot(df_standard['controller_lyapunov'][:])
plt.xlabel("Time (hrs)")
plt.ylabel("Lyapunov value function")
plt.tight_layout()
plt.savefig(os.path.join(savefig_path, "kai-lyapunov_value_function_std_enmpc.pdf"))

#Plot sink pressures
plt.figure()
x = np.linspace(41, 41, len(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]']))
plt.plot(x, '--k')
plt.plot(df_standard['node pressure']['node_p[' + "'sink_1'" + ', :]'], label = 'Sink 1')
plt.plot(df_standard['node pressure']['node_p[' + "'sink_2'" + ', :]'], label = 'Sink 2')
plt.plot(df_standard['node pressure']['node_p[' + "'sink_3'" + ', :]'], label = 'Sink 3')
plt.plot(df_standard['node pressure']['node_p[' + "'sink_4'" + ', :]'], label = 'Sink 4')
plt.plot(df_standard['node pressure']['node_p[' + "'sink_5'" + ', :]'], label = 'Sink 5')

plt.legend()
plt.ylabel("Pressure (bar)")
plt.xlabel('$\mathrm{Time(hrs)}$')

fig , ax = plt.subplots(1,5, figsize = (20, 4))
ax[0].plot(df_standard['node pressure']['node_p[' + "'sink_1'" + ', :]'], 'r', label = 'Sink 1')
ax[1].plot(df_standard['node pressure']['node_p[' + "'sink_2'" + ', :]'], 'b',label = 'Sink 2')
ax[2].plot(df_standard['node pressure']['node_p[' + "'sink_3'" + ', :]'], 'g',label = 'Sink 3')
ax[3].plot(df_standard['node pressure']['node_p[' + "'sink_4'" + ', :]'], 'magenta',label = 'Sink 4')
ax[4].plot(df_standard['node pressure']['node_p[' + "'sink_5'" + ', :]'], 'darkorange',label = 'Sink 5')
for i in range(5):
    ax[i].plot(x, '--k')
    ax[i].set_title('Sink %i'%(i+1), fontsize = 24)
    ax[i].set_ylim(40.9, 43)
    ax[i].set_xlabel("Time (hrs)", fontsize = 24)
ax[0].set_ylabel("Pressure (bar)", fontsize = 24)
plt.tight_layout()
plt.savefig(os.path.join(savefig_path, "kai_sink_pressures_enmpc_no_unc.pdf"))
