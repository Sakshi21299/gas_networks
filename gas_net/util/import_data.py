# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 10:34:09 2021

@author: Lavinia

"""

import pandas as pd

def DataFrame_2levels_to_dict(df):
    """
    Rearrange pipe dataframe with indices: (pipe, vol) and columns: time
    into a dictionary of type {pipe: vol: {t0: .., t1: }}
    """

    dct_interm = pd.DataFrame.to_dict(df, orient = "index")
    dct = {keys[0]: {} for keys in dct_interm.keys()}
    for keys in dct_interm.keys():
        dct[keys[0]][keys[1]] = dct_interm[keys] 
    return dct

#==============================================================================
""" NETWORK DATA """
#==============================================================================

def import_network_data_from_excel(data_path):
    # ARCS
    df_arcs = pd.read_excel(data_path, sheet_name = "Arcs", index_col = 0)
    Arcs = pd.DataFrame.to_dict(df_arcs, orient = "index") 
    # PIPES
    df_pipes = pd.read_excel(data_path, sheet_name = "Pipes", index_col = 0)
    Pipes = pd.DataFrame.to_dict(df_pipes, orient = "index")      
    # NODES
    df_nodes = pd.read_excel(data_path, sheet_name = "Nodes", index_col = 0)
    Nodes = pd.DataFrame.to_dict(df_nodes, orient = "index")
    
    # STATIONS
    df_stations = pd.read_excel( data_path, sheet_name = "Stations", index_col = 0)
    Stations = pd.DataFrame.to_dict(df_stations, orient = "index")    

    # VALVES
    Valves = {}
    try:
        df_v = pd.read_excel(
            data_path, sheet_name = "Valves", index_col = 0)
        Valves = pd.DataFrame.to_dict(df_v, orient = "index")   
    except:
        print('!!! Valves sheet missing in networkData')
           
    # DATA
    Data = {"Arcs": Arcs, "Pipes": Pipes, "Nodes": Nodes, 
            "Valves" : Valves, 
            "Stations": Stations}   
    return Data

#==============================================================================
"""  TIME VARYING DATA """
#==============================================================================

## ADJUST DATA
def rearrange_setpoint_data(df):
    """ Rearrange setpoints dataframe with indices: (source, setpoint_type) and columns: time
    into 2 dictionaries (p setpoint and w setpoint) of type {source: {t0: .., t1: }}"""
    pCV = {}
    wCV = {}
    for elem, var in df.index:
        if var == "p":
            pCV[elem] = {t: df.loc[elem,"p"][t] for t in df.columns} 
        elif var == "w":
            wCV[elem] = {t: df.loc[elem,"w"][t] for t in df.columns} 
    return pCV, wCV

def set_pipe_cons_to_default(wcons, Pipes, value = 0):
    """ 
    Set wcons = 0 in all Pipes volumes that are not specified in wcons dictionary 
    """
    if len(list(Pipes.keys())) >= 1:
        ref_pipe = list(Pipes.keys())[0]
        times = wcons[ref_pipe][list(wcons[ref_pipe].keys())[0]].keys()
              
        for pipe in Pipes.keys(): # add wcons = 0 in other pipes volumes
            if pipe not in wcons.keys():
                wcons[pipe] = {}
            for vol in range(1, int(Pipes[pipe]["Nvol"])):
                if vol not in wcons[pipe].keys():
                    wcons[pipe][vol] = {}
                    for counter, t in enumerate(times):
                        wcons[pipe][vol][t] = value
    return wcons

## IMPORT DATA
def import_time_varying_data_from_excel(data_path):
    # SOURCES
    df_sources = pd.read_excel(data_path, sheet_name = "SourcesSP",index_col = [0,1], header = 0)
    pSource, wSource = rearrange_setpoint_data(df_sources)                 
    # WCONS (pipe/nodes)
    df_wcons = pd.read_excel(data_path, sheet_name = "wcons",index_col = [0,1], header = 0)
    wcons = DataFrame_2levels_to_dict(df_wcons)     
    Data = {
        "pSource": pSource,"wSource": wSource, "wCons":wcons}
    return Data


#==============================================================================
""" ALL """
#==============================================================================

def import_data_from_excel(network_data_path, input_data_path):
    # topology
    networkData = import_network_data_from_excel(network_data_path)
    # profiles
    inputData = import_time_varying_data_from_excel(input_data_path)
    # add missing consumption in pipes finite volumes
    try:
        inputData['wCons'] = set_pipe_cons_to_default(inputData['wCons'], networkData['Pipes'])
    except:
        print('!!! ERROR importing inputData. No matching with networkData')
    return networkData, inputData
