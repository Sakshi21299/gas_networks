# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 09:13:13 2025

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
file_name = r"final_paper_kai_enmpc_periodic_with_stability_72hrs_random_uncertain_demands_seed42.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

savefig_path = r"C:\Users\ssnaik"#\Biegler\gas_networks_italy\gas_networks\gas_net\results\plots\economic_nmpc_experiments\standard_enmpc"
#Plot demand at sink nodes
fig, ax = plt.subplots()
#ax.plot(df_standard['wCons'][:], 'salmon')
ax.plot(df_standard['wCons'][df_standard['wCons'].columns[1]], 'salmon', label = '$\mathrm{Demand \: achieved}$')
#ax.plot(df_standard['wCons_target'][:], 'green', label = '$\mathrm{Target \: demand}$')
ax.set_ylabel("$\mathrm{Flow (kg/s)}$")
ax.set_xlabel('$\mathrm{Time(hrs)}$')
#ax.legend(loc = 'upper right')
ax.set_ylim(25,49)
fig.tight_layout()
#fig.savefig(os.path.join(savefig_path, "kai-target-demand-enmpc.pdf"))

#Plot controls
plt.figure()
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]'], color = 'salmon', label = '$\mathrm{C} 1$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_2'" + ', :]'], color = 'b', label = '$\mathrm{C} 2$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_3'" + ', :]'], color = 'brown', label = '$\mathrm{C} 3$')

plt.ylabel("$\mathrm{Compressor } P_{out}/P_{in} $")
plt.xlabel('$\mathrm{Time(hrs)}$')
plt.legend(bbox_to_anchor=(0.96, 0.05), loc = 'lower right', fontsize = 12)
plt.tight_layout()
#plt.savefig(os.path.join(savefig_path,"compressor_beta_unc_std_enmpc.pdf"))

#Plot sink pressures
x = np.linspace(41, 41, len(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]']))

fig , ax = plt.subplots(1,5, figsize = (20, 4))
ax[0].plot(df_standard['node pressure']['node_p[' + "'sink_1'" + ', :]'], 'r', label = 'Sink 1')
ax[1].plot(df_standard['node pressure']['node_p[' + "'sink_2'" + ', :]'], 'b',label = 'Sink 2')
ax[2].plot(df_standard['node pressure']['node_p[' + "'sink_3'" + ', :]'], 'g',label = 'Sink 3')
ax[3].plot(df_standard['node pressure']['node_p[' + "'sink_4'" + ', :]'], 'magenta',label = 'Sink 4')
ax[4].plot(df_standard['node pressure']['node_p[' + "'sink_5'" + ', :]'], 'darkorange',label = 'Sink 5')
for i in range(5):
    ax[i].plot(x, '--k')
    ax[i].set_title('Sink %i'%(i+1), fontsize = 24)
    ax[i].set_ylim(40.4, 43)
    ax[i].set_xlabel("Time (hrs)", fontsize = 24)
ax[0].set_ylabel("Pressure (bar)", fontsize = 24)
plt.tight_layout()
#plt.savefig(os.path.join(savefig_path, "kai_sink_pressures_enmpc_unc.pdf"))

#Plot multiple profiles
file_name = r"final_paper_kai_enmpc_periodic_with_stability_72hrs_random_uncertain_demands_seed62.xlsx"
file_path = os.path.join(path, file_name)
df_standard_2 = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

x = np.linspace(41, 41, len(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]']))
shades = np.linspace(0.3, 1, 5)
fig , ax = plt.subplots(1,5, figsize = (20, 4))
ax[0].plot(df_standard['node pressure']['node_p[' + "'sink_1'" + ', :]'], color =(1, shades[0], shades[0]))
ax[0].plot(df_standard_2['node pressure']['node_p[' + "'sink_1'" + ', :]'], color =(1, shades[4], shades[4]))

ax[1].plot(df_standard['node pressure']['node_p[' + "'sink_2'" + ', :]'], 'b',label = 'Sink 2')
ax[1].plot(df_standard_2['node pressure']['node_p[' + "'sink_2'" + ', :]'], 'turquoise',label = 'Sink 2')

ax[2].plot(df_standard['node pressure']['node_p[' + "'sink_3'" + ', :]'], 'g',label = 'Sink 3')
ax[2].plot(df_standard_2['node pressure']['node_p[' + "'sink_3'" + ', :]'], 'mediumspringgreen',label = 'Sink 3')

ax[3].plot(df_standard['node pressure']['node_p[' + "'sink_4'" + ', :]'], 'magenta',label = 'Sink 4')
ax[3].plot(df_standard_2['node pressure']['node_p[' + "'sink_4'" + ', :]'], 'orchid',label = 'Sink 4')


ax[4].plot(df_standard['node pressure']['node_p[' + "'sink_5'" + ', :]'], 'darkorange',label = 'Sink 5')
ax[4].plot(df_standard_2['node pressure']['node_p[' + "'sink_5'" + ', :]'], 'lightsalmon',label = 'Sink 5')

for i in range(5):
    ax[i].plot(x, '--k')
    ax[i].set_title('Sink %i'%(i+1), fontsize = 24)
    ax[i].set_ylim(40.4, 43)
    ax[i].set_xlabel("Time (hrs)", fontsize = 24)
ax[0].set_ylabel("Pressure (bar)", fontsize = 24)
plt.tight_layout()
#plt.savefig(os.path.join(savefig_path, "kai_sink_pressures_enmpc_unc.pdf"))

plt.figure()
plt.plot(df_standard['node pressure']['node_p[' + "'sink_1'" + ', :]'], 'r', label = 'Sink 1')
plt.plot(x, '--k')
plt.xlabel('Time(hrs)')
plt.ylabel('Pressure(bar)')
plt.ylim(40.5, 43)
plt.tight_layout()
plt.savefig('kai_pressure_sink_1_standard.png', dpi = 300)


