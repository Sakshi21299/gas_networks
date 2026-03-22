# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 13:03:42 2024

@author: ssnaik
"""

import matplotlib.pyplot as plt
import pandas as pd
import os

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net"

file_name = "optimal_css_24hrs_inf_horizon.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

savefig_path = r"C:\Users\ssnaik" #"\Biegler\gas_networks_italy\gas_networks\gas_net\results\plots\optimal_css_plots"
#Plot demand at sink nodes
plt.figure()
plt.plot(df_standard['wCons'][:])
plt.ylim(15.4, 17.25)
plt.ylabel("Flow at sink nodes")
plt.xlabel('Time(hrs)')
plt.title("Flow at sink nodes in the plant - Standard ENMPC")

#Plot node pressures
plt.figure()
plt.plot(df_standard['node pressure'][:])
plt.ylabel("Pressure at sink nodes")
plt.xlabel('Time(hrs)')
plt.title("Pressure at sink nodes in the plant - Standard ENMPC")
plt.savefig(os.path.join(savefig_path, "pressure_sink_nodes.png"),  dpi = 300)

#Plot source flows
plt.figure()
plt.plot(df_standard['wSource'][:])
plt.ylabel("Flow at source nodes")
plt.xlabel('Time(hrs)')
plt.title("Flow at source nodes in the plant - Standard ENMPC")
plt.savefig(os.path.join(savefig_path,"flow_source_nodes.png"),  dpi = 300)

#Plot source pressures
plt.figure()
plt.plot(df_standard['pSource'][:])
plt.ylim(54, 59)
plt.ylabel("Pressure at source nodes")
plt.xlabel('Time(hrs)')
plt.title("Pressure at source nodes in the plant - Standard ENMPC")
plt.savefig(os.path.join(savefig_path,"pressure_source_nodes.png"),  dpi = 300)


#Plot intermediate pressures 
plt.figure()
plt.plot(df_standard['interm_p'][:])
plt.ylabel("Intermediate pressures in pipes")
plt.xlabel('Time(hrs)')
plt.title("Intermediate pressure in pipes in plant - Standard ENMPC")

#Plot intermediate flows 
plt.figure()
plt.plot(df_standard['interm_w'][:])
plt.ylabel("Intermediate flows in pipes")
plt.xlabel('Time(hrs)')
plt.title("Intermediate flows in pipes in plant - Standard ENMPC")

#Plot controls
plt.figure()
plt.plot(df_standard['compressor beta'][:])
plt.ylabel("Compressor beta")
plt.xlabel('Time(hrs)')
plt.title("Compressor controls - Standard ENMPC")
plt.savefig(os.path.join(savefig_path,"compressor_betas.png"), dpi = 300)

#Plot compressor power
plt.figure()
plt.plot(df_standard['compressor power'][:])
plt.ylabel("Compressor power")
plt.xlabel('Time(hrs)')
plt.title("Compressor power - Standard ENMPC")
plt.savefig(os.path.join(savefig_path,"compressor_power.png"), dpi = 300)

