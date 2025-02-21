# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 11:23:16 2024

@author: ssnaik
"""
import pandas as pd
import os
path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net"
def write_data_to_excel(sim_data, m_plant, sheets_keys_dict, file_name, terminal_pressure_slack_dict = None, terminal_flow_slack_dict = None, 
                        controller_1_lyapunov = None,
                        controller_2_lyapunov = None,
                        controller_3_lyapunov = None,
                        controller_multistage_lyapunov = None):
    writer = pd.ExcelWriter(os.path.join(path, file_name))
    for sheet_name, keys in sheets_keys_dict.items():
        df = pd.DataFrame()
      
        for i, key in enumerate(keys):
            data_list = sim_data.get_data_from_key(key)
            df[str(key)] = data_list
        df.to_excel(writer, sheet_name=sheet_name)
            
    df = pd.DataFrame()
    if terminal_pressure_slack_dict is not None:
        df['terminal_pressure_slacks'] = terminal_pressure_slack_dict.values()
    
    if terminal_flow_slack_dict is not None:
        df['terminal_flow_slacks'] = terminal_flow_slack_dict.values()
    df.to_excel(writer, sheet_name="terminal_slacks")
    
    df = pd.DataFrame()
    if controller_1_lyapunov is not None:
        df['controller_1_lyapunov'] = controller_1_lyapunov.values()
    if controller_2_lyapunov is not None:
        df['controller_2_lyapunov'] = controller_2_lyapunov.values()
    if controller_3_lyapunov is not None:
        df['controller_3_lyapunov'] = controller_3_lyapunov.values()
    if controller_multistage_lyapunov is not None:
        df['controller_multistage_lyapunov'] = controller_multistage_lyapunov.values()
    
    df.to_excel(writer, sheet_name="controller_lyapunov")
    writer.close()
    
    

    