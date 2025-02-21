# -*- coding: utf-8 -*-
"""
Created on Mon Dec 30 08:54:55 2024

@author: ssnaik
"""
import matplotlib.pyplot as plt
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

file_name = r"final_paper_results\final_paper_enmpc_explicit_terminal_each_point_stability_72hrs.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results\optimal_css_24hrs_extended.xlsx"
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
plt.ylim(15.4, 17.3)
plt.legend()
plt.tight_layout()
#plt.savefig(os.path.join(savefig_path, "flow_at_sink_nodes_no_unc_std_enmpc.pdf"))

#Plot controls
plt.figure()
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]'], color = 'salmon', label = '$\mathrm{C} 1$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_2'" + ', :]'], color = 'b', label = '$\mathrm{C} 2$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_3'" + ', :]'], color = 'brown', label = '$\mathrm{C} 3$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_4'" + ', :]'], color = 'y', label = '$\mathrm{C} 4$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_5'" + ', :]'], color = 'r', label = '$\mathrm{C} 5$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_6'" + ', :]'], color = 'g', label = '$\mathrm{C} 6$')
#plt.ylim(1, 1.9)
plt.ylabel("$\mathrm{Compressor }$" + r" $\beta $")
plt.xlabel('$\mathrm{Time(hrs)}$')
#plt.title("Compressor controls - Standard ENMPC")
plt.legend(bbox_to_anchor=(0.96, 0.05), loc = 'lower right', fontsize = 12)
plt.tight_layout()
plt.savefig(os.path.join(savefig_path,"compressor_beta_no_unc_std_enmpc.pdf"))

#Plot source flow css
fig , ax = plt.subplots(1,3, figsize = (20, 5))
ax[0].plot(df_optimal_css['wSource']['wSource[' + "'source_1'" + ', :]'], ':', color='k', label = 'Optimal CSS')
ax[0].plot(df_standard['wSource']['wSource[' + "'source_1'" + ', :]'], '--b')
ax[0].set_ylabel("$\mathrm{Flow (kg/s)}$", fontsize = 20)
ax[0].set_xlabel('$\mathrm{Time(hrs)}$', fontsize = 20)
ax[0].set_title('Source 1 (S1)')

ax[1].plot(df_optimal_css['wSource']['wSource[' + "'source_2'" + ', :]'], ':', color='k')
ax[1].plot(df_standard['wSource']['wSource[' + "'source_2'" + ', :]'], '--g')
ax[1].set_ylabel("$\mathrm{Flow (kg/s)}$", fontsize = 20)
ax[1].set_xlabel('$\mathrm{Time(hrs)}$', fontsize = 20)
ax[1].set_title('Source 2 (S2)')

ax[2].plot(df_optimal_css['pSource']['pSource[' + "'source_3'" + ', :]'], ':', color='k')
ax[2].plot(df_standard['pSource']['pSource[' + "'source_3'" + ', :]'], '--r')
ax[2].set_ylabel("$\mathrm{Pressure (bar)}$", fontsize = 20)
ax[2].set_xlabel('$\mathrm{Time(hrs)}$', fontsize = 20)
ax[2].set_title('Source 3 (S3)')
ax[0].legend(bbox_to_anchor=(0.3, -0.1))

ax[0].axvline(x=48, color='orange', linestyle='-') 
ax[1].axvline(x=48, color='orange', linestyle='-')
ax[2].axvline(x=48, color='orange', linestyle='-')
fig.tight_layout()
plt.savefig(os.path.join(savefig_path,"ocss_supply.pdf"))



#Plot lyapunov value function
plt.figure()
plt.plot(df_standard['controller_lyapunov'][:])
plt.xlabel("Time (hrs)")
plt.ylabel("Lyapunov value function")
plt.tight_layout()
plt.savefig(os.path.join(savefig_path, "lyapunov_value_function_std_enmpc.pdf"))