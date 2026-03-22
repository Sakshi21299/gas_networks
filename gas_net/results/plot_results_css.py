# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 10:12:36 2024

@author: ssnaik
"""

import matplotlib.pyplot as plt
import pandas as pd
import os

# Global Matplotlib configuration
FONTSIZE = 20
plt.rcParams.update({
    # Font and text
    "font.size": FONTSIZE,            # Default font size for all text
    "font.family":'serif',
    "axes.titlesize": FONTSIZE,       # Title font size
    "axes.labelsize": FONTSIZE,       # X and Y label font size
    "xtick.labelsize": FONTSIZE,      # X-tick label font size
    "ytick.labelsize": FONTSIZE,      # Y-tick label font size
    "legend.fontsize": FONTSIZE,      # Legend font size

    # Lines and colors
    "lines.linewidth": 2.0,     # Default line thickness
    "axes.prop_cycle": plt.cycler(
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
               "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
               "#bcbd22", "#17becf"]
    ),  # Default color cycle (customized)

    # Figure layout
    "figure.figsize": (8, 5),   # Default figure size (width, height)
    "figure.dpi": 120,          # Resolution
    "axes.grid": True,          # Add grid by default
    "grid.linestyle": "--",     # Grid style
    "grid.alpha": 0.7           # Grid transparency
})

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net"

file_name = r"results\gaslib40_finite_12hrs_new.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = r"results\optimal_css_12hrs_gaslib40_infhorizon_small_demand.xlsx"

file_path = os.path.join(path, file_name)
df_optimal_css_24 = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

df_optimal_css = {}

for key in df_optimal_css_24:
    base = df_optimal_css_24[key]
    
    df_optimal_css[key] = pd.concat(
        [base] + [base.iloc[1:]]*3,   # skip 0th row in repeats
        ignore_index=True
    )

savefig_path = r"C:\Users\ssnaik\Biegler\someinfhorizonmaterial\Results-Thesis\Gasnet"
#Plot demand at sink nodes
plt.figure()
plt.plot(df_standard['wCons'][:], 'salmon')
plt.plot(df_optimal_css['wCons'][df_optimal_css['wCons'].columns[1]], ':k', label = 'Target demand')
plt.ylabel("Flow (kg/s)")
plt.xlabel('Time(hrs)')
plt.title("Flow at sink nodes in the plant - Standard ENMPC")
#plt.ylim(15.4, 17.3)
plt.legend()
#plt.savefig(os.path.join(savefig_path, "flow_at_sink_nodes.svg"))

#Plot node pressures
plt.figure()
plt.plot(df_standard['node pressure'][:])
plt.plot(df_optimal_css['node pressure'][:], ':k')
plt.ylabel("Pressure at sink nodes")
plt.xlabel('Time(hrs)')
plt.title("Pressure at sink nodes in the plant - Standard ENMPC")
#plt.savefig(os.path.join(savefig_path,"pressure_at_sink_nodes.svg"))

#Plot source flows
plt.figure()
plt.plot(df_standard['wSource'][:], label = 'Source flow')
plt.plot(df_optimal_css['wSource'][:], ':k', label = 'OCSS')
plt.ylabel("Flow (kg/s)")
plt.xlabel('Time(hrs)')
plt.legend()
#plt.savefig(os.path.join(savefig_path,"infinite-horizon-1cycle-flow-source-gasnet.pdf"))
#
#Plot source pressures
plt.figure()
plt.plot(df_standard['pSource'][:])
plt.plot(df_optimal_css['pSource'][:], ':k')
#plt.ylim(54, 59)
plt.ylabel("Pressure at source nodes")
plt.xlabel('Time(hrs)')
plt.title("Pressure at source nodes in the plant - Standard ENMPC")
#plt.savefig(os.path.join(savefig_path,"pressure_at_source_nodes.svg"))


#Plot intermediate pressures 
plt.figure()
plt.plot(df_standard['interm_p'][:])
plt.plot(df_optimal_css['interm_p'][:], ':k')
plt.ylabel("Intermediate pressures in pipes")
plt.xlabel('Time(hrs)')
plt.title("Intermediate pressure in pipes in plant - Standard ENMPC")

#Plot intermediate flows 
# plt.figure()
# plt.plot(df_standard['interm_w'][:])
# plt.plot(df_optimal_css['interm_w'][:], ':k')
# plt.ylabel("Intermediate flows in pipes")
# plt.xlabel('Time(hrs)')
# plt.title("Intermediate flows in pipes in plant - Standard ENMPC")

#Plot controls
plt.figure()
plt.plot(df_standard['compressor beta'][:], label = df_standard['compressor beta'].columns)
plt.plot(df_optimal_css['compressor beta'][:], ':k')
plt.ylabel("Compressor beta")
plt.xlabel('Time(hrs)')
plt.legend()
plt.title("Compressor controls - Standard ENMPC")
plt.savefig(os.path.join(savefig_path,"compressor_beta.svg"))

#Plot compressor power
plt.figure()
plt.plot(df_standard['compressor power'][:]*10**3)
plt.plot(df_optimal_css['compressor power'][df_optimal_css['compressor power'].columns[0]]*10**3, ':k', label = 'OCSS')
plt.plot(df_optimal_css['compressor power'][df_optimal_css['compressor power'].columns[1:]]*10**3, ':k')
plt.ylabel("Energy(kWh)")
plt.xlabel('Time(hrs)')
plt.legend(['C1', 'C2', 'C3', 'OCSS'], loc = 'upper right')
plt.tight_layout()
# plt.savefig(os.path.join(savefig_path,"infinite-horizon-1cycle-comp-power-gasnet.pdf"))

#Plot lyapunov value function
# plt.figure()
# plt.plot(df_standard['controller_lyapunov'][:])
# plt.ylabel("V(k)")
# plt.xlabel("Time (hrs)")
# plt.title("Lyapunov value function")
#plt.savefig(os.path.join(savefig_path, "lyapunov_value_function.svg"))