# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 12:51:14 2024

@author: ssnaik
"""
import matplotlib.pyplot as plt
import pandas as pd
import os

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results"

file_name = r"final_results\enmpc_experiments\enmpc_periodic_no_stability_gaslib40_72hrs.xlsx"
file_path = os.path.join(path, file_name)
df_enmpc_no_stability = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = r"final_results\enmpc_experiments\enmpc_periodic_plus_stability_gaslib40_72hrs.xlsx"
file_path = os.path.join(path, file_name)
df_enmpc_stability = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = r"final_results\tracking_experiments\tracking_gaslib_40_psource_css_72_hrs.xlsx"
file_path = os.path.join(path, file_name)
df_tracking = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

#Plot compressor power
plt.figure()
plt.plot(df_enmpc_stability['compressor power'].sum(axis = 'columns'), label = 'ENMPC-Stability')
plt.plot(df_tracking['compressor power'].sum(axis = 'columns'), '--',label = 'Tracking')
plt.ylabel("Compressor power")
plt.xlabel('Time(hrs)')
plt.title("Compressor power - Standard ENMPC")
plt.legend()
#plt.savefig(os.path.join(savefig_path,"compressor_power.png"), dpi = 300)

#Supply flows
plt.figure()
plt.plot(df_enmpc_stability['wSource'].sum(axis = 'columns'), label = 'ENMPC-Stability')
plt.plot(df_tracking['wSource'].sum(axis = 'columns'), '--',label = 'Tracking')
plt.ylabel("Flow at source nodes")
plt.xlabel('Time(hrs)')
plt.title("Flow at source nodes in the plant - Standard ENMPC")
plt.legend()

#Intermediate flows
plt.figure()
plt.plot(df_enmpc_stability['interm_w'].sum(axis = 'columns'), label = 'ENMPC-Stability')
plt.plot(df_tracking['interm_w'].sum(axis = 'columns'), '--',label = 'Tracking')
plt.ylabel("Intermediate flows in pipes")
plt.xlabel('Time(hrs)')
plt.title("Intermediate flows in pipes in plant - Standard ENMPC")
plt.legend()

#Source pressures
plt.figure()
plt.plot(df_enmpc_stability['pSource'].sum(axis = 'columns'), label = 'ENMPC-Stability')
plt.plot(df_tracking['pSource'].sum(axis = 'columns'), '--',label = 'Tracking')
plt.ylabel("Source pressures")
plt.xlabel('Time(hrs)')
plt.title("Source pressures in plant")
plt.legend()