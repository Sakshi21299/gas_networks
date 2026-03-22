# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 13:47:09 2024

@author: ssnaik
"""

import matplotlib.pyplot as plt
import pandas as pd
import os

path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\results"

file_name = "standard_enmpc_min_scenario.xlsx"
file_path = os.path.join(path, file_name)
df_standard = pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")

file_name = "multistage_min_scenario.xlsx"
file_path = os.path.join(path, file_name)

df_multistage =  pd.read_excel(file_path, sheet_name=None, index_col="Unnamed: 0")


#Plot terminal pressure slacks
plt.figure()
plt.plot(df_standard['terminal_slacks']['terminal_pressure_slacks'], label = 'Standard ENMPC')
plt.plot(df_multistage['terminal_slacks']['terminal_pressure_slacks'], label = 'Multistage ENMPC')
plt.title("Terminal pressure slacks in the controller")
plt.xlabel("Time(hrs)")
plt.legend()

#Plot terminal flow slacks
plt.figure()
plt.plot(df_standard['terminal_slacks']['terminal_flow_slacks'], label = 'Standard ENMPC')
plt.plot(df_multistage['terminal_slacks']['terminal_flow_slacks'], label = 'Multistage ENMPC')
plt.title("Terminal flow slacks in the controller")
plt.xlabel("Time(hrs)")
plt.legend()

#Demand penalty in the plant
plt.figure()
demand_pen_standard = df_standard['demand slacks'].sum(axis = 1)
demand_pen_multistage = df_multistage['demand slacks'].sum(axis = 1)
plt.plot(demand_pen_standard, label = 'Standard ENMPC')
plt.plot(demand_pen_multistage, label = 'Multistage ENMPC')
plt.title("Total demand penalty in the plant")
plt.xlabel("Time(hrs)")
plt.ylabel("Demand penalty")
plt.legend()

#Plot demand at sink nodes
plt.figure()
plt.plot(df_standard['wCons'][:])
plt.ylim(15.4, 17.25)
plt.ylabel("Flow at sink nodes")
plt.xlabel('Time(hrs)')
plt.title("Flow at sink nodes in the plant - Standard ENMPC")

plt.figure()
plt.plot(df_multistage['wCons'][:])
plt.ylim(15.4, 17.25)
plt.ylabel("Flow at sink nodes")
plt.xlabel('Time(hrs)')
plt.title("Flow at sink nodes in the plant - Multistage ENMPC")

#Plot compressor controls
plt.figure()
plt.plot(df_standard['compressor beta'][:])
plt.ylim(1, 1.9)
plt.ylabel("Compressor beta")
plt.xlabel('Time(hrs)')
plt.title("Compressor controls - Standard ENMPC")

plt.figure()
plt.plot(df_multistage['compressor beta'][:])
plt.ylim(1, 1.9)
plt.ylabel("Compressor beta")
plt.xlabel('Time(hrs)')
plt.title("Compressor controls - Multistage ENMPC")

#Plot total power consumed 
plt.figure()
power_standard = df_standard['compressor power'].sum(axis = 1)
power_multistage = df_multistage['compressor power'].sum(axis = 1)
plt.plot(power_standard, label = 'Standard ENMPC')
plt.plot(power_multistage, label = 'Multistage ENMPC')
plt.title("Total power consumed in plant")
plt.xlabel("Time(hrs)")
plt.ylabel("Power consumed")
plt.legend()
