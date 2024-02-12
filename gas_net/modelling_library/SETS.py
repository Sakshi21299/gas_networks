import pyomo.environ as pyo
import pyomo.dae as dae
import numpy as np


#==============================================================================
""" SETS """
#==============================================================================

############################### TIME ######################################
###########################################################################   

def TIME_sets(m, Opt):
    T0 = Opt["T0"]
    T = Opt["T"]
    dt = Opt["dt"]
    times = np.arange(T0,T+dt/3600,dt/3600)
    m.Times = dae.ContinuousSet(initialize=times)
    return m

############################### NETWORK ###################################
###########################################################################

def NODE_sets(m, networkData):
    Nodes = networkData["Nodes"]  
    Arcs = networkData['Arcs']
    # DATA
    for n in Nodes.keys():
        Nodes[n]["arcsOUT"] = []
        Nodes[n]["arcsIN"] = []
    for arc in Arcs.keys():
        n_in = Arcs[arc]["nodeIN"]
        n_out = Arcs[arc]["nodeOUT"]
        Nodes[n_in]["arcsOUT"].append(arc)
        Nodes[n_out]["arcsIN"].append(arc)
    Nodes_ArcsIN = {n: Nodes[n]["arcsIN"] for n in Nodes.keys()}
    Nodes_ArcsOUT = {n: Nodes[n]["arcsOUT"] for n in Nodes.keys()}
    NodesSources = [n for n in Nodes.keys() if str(Nodes[n]["source"]) != "nan"]
    # SET
    m.Nodes = pyo.Set(initialize = Nodes.keys())
    # SUB-SET
    m.NodesSources = pyo.Set(initialize = NodesSources)
    # MULTI-LAYER SETS
    m.Nodes_ArcsIN = pyo.Set(m.Nodes, initialize = Nodes_ArcsIN)
    m.Nodes_ArcsOUT = pyo.Set(m.Nodes, initialize = Nodes_ArcsOUT)
    return m

def ARC_sets(m, networkData):
    Arcs = networkData['Arcs']
    m.Arcs = pyo.Set(initialize = list(Arcs.keys()))
    # NODES IN/OUT from each ARC (not actually a pyomo Set)
    m.Arcs_NodeIN = {arc: Arcs[arc]["nodeIN"] for arc in Arcs.keys()}
    m.Arcs_NodeOUT= {arc: Arcs[arc]["nodeOUT"] for arc in Arcs.keys()}     
    return m

############################### VALVES ######################################
###########################################################################

def VALVE_sets(m, networkData):
    m.Valves = pyo.Set(initialize = networkData["Valves"].keys())
    return m

##################### STATIONS/MACHINES ###################################
###########################################################################

def STATION_set(m, networkData):
    m.Stations = pyo.Set(initialize = networkData["Stations"].keys())
    return m

######################### PIPES ###########################################
###########################################################################

def PIPE_sets(m, networkData):
    Pipes = networkData["Pipes"]        
    # SET: PIPES
    m.Pipes = pyo.Set(initialize = Pipes.keys())    
    m.Pipes_Directed = pyo.Set(initialize = (p for p in m.Pipes if (Pipes[p]["Direction"] == 1 or Pipes[p]["Direction"] == -1)))
    return m

def PIPE_finite_volumes_sets(m, networkData):
    Pipes = networkData["Pipes"]    
    # DATA: VOLUMES PIPES
    Pipes_VolExtrR = []
    Pipes_VolExtrC = []
    Pipes_VolCenterC = []
    Pipes_VolExtrR_interm = [] # to define interm  pressure
    Pipes_VolExtrC_interm = [] # to define interm  w
    for p in Pipes.keys():
        N = Pipes[p]["Nvol"]
        for index in range(1,N+2):
            Pipes_VolExtrR.append((p,index))
            if index != 1 and index != N+1:
                Pipes_VolExtrR_interm.append((p,index))
            if index != N+1:
                Pipes_VolExtrC.append((p,index))
                if index != N:
                    Pipes_VolCenterC.append((p,index))
                    if index != 1:
                        Pipes_VolExtrC_interm.append((p,index))
    # SET: PIPES VOLUMES SETS
    m.Pipes_VolExtrR = pyo.Set(initialize = Pipes_VolExtrR)
    m.Pipes_VolExtrC = pyo.Set(initialize = Pipes_VolExtrC)
    m.Pipes_VolExtrR_interm = pyo.Set(initialize = Pipes_VolExtrR_interm)
    m.Pipes_VolExtrC_interm = pyo.Set(initialize = Pipes_VolExtrC_interm)
    m.Pipes_VolCenterC = pyo.Set(initialize = Pipes_VolCenterC)
    return m
