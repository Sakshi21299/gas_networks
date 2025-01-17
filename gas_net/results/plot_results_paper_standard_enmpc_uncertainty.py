# -*- coding: utf-8 -*-
"""
Created on Tue Jan 14 09:13:13 2025

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

file_name = r"final_paper_results\final_paper_enmpc_periodic_without_stability_72hrs_random_uncertain_demands_0.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

savefig_path = r"C:\Users\ssnaik"#\Biegler\gas_networks_italy\gas_networks\gas_net\results\plots\economic_nmpc_experiments\standard_enmpc"
#Plot demand at sink nodes
fig, ax = plt.subplots()
ax.plot(df_standard['wCons'][:], 'salmon')
ax.plot(df_standard['wCons'][df_standard['wCons'].columns[1]], 'salmon', label = '$\mathrm{Demand \: achieved}$')
ax.plot(df_standard['wCons_target'][:], ':k', label = '$\mathrm{Target \: demand}$')

square = pt.Rectangle((49, 16.8), 10, 0.45, linewidth=1, edgecolor='b', facecolor='none')
ax.add_patch(square)
ax.set_ylabel("$\mathrm{Flow (kg/s)}$")
ax.set_xlabel('$\mathrm{Time(hrs)}$')
ax.set_ylim(15.4, 17.3)
#ax.legend()
fig.tight_layout()
#fig.savefig(os.path.join(savefig_path, "flow_at_sink_nodes_unc_std_enmpc.pdf"))

#Plot controls
plt.figure()
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_1'" + ', :]'], color = 'salmon', label = '$\mathrm{C} 1$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_2'" + ', :]'], color = 'b', label = '$\mathrm{C} 2$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_3'" + ', :]'], color = 'brown', label = '$\mathrm{C} 3$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_4'" + ', :]'], color = 'y', label = '$\mathrm{C} 4$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_5'" + ', :]'], color = 'r', label = '$\mathrm{C} 5$')
plt.plot(df_standard['compressor beta']['compressor_beta[' + "'compressorStation_6'" + ', :]'], color = 'g', label = '$\mathrm{C} 6$')
plt.ylabel("$\mathrm{Compressor } P_{out}/P_{in} $")
plt.xlabel('$\mathrm{Time(hrs)}$')
plt.legend(bbox_to_anchor=(0.96, 0.05), loc = 'lower right', fontsize = 12)
plt.tight_layout()
#plt.savefig(os.path.join(savefig_path,"compressor_beta_unc_std_enmpc.pdf"))


