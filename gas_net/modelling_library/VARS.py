import pyomo.environ as pyo
import pyomo.dae as dae

#==============================================================================
""" VARIABLES """
#==============================================================================

######################### NETWORK ###########################################
###########################################################################

def NODE_vars(m):
    # ALL NODES
    m.node_p = pyo.Var(m.Nodes, m.Times, within = pyo.NonNegativeReals)
    # Remark: node demand (wCons) is defined toghetwer with pipes demand
    # SUPPLY NODES
    m.pSource = pyo.Var(m.NodesSources, m.Times, within = pyo.NonNegativeReals) 
    m.wSource = pyo.Var(m.NodesSources, m.Times, within = pyo.Reals) 
    return m

def ARC_vars(m):
    # ARCS
    m.inlet_w = pyo.Var(m.Arcs, m.Times, within = pyo.Reals)
    m.outlet_w = pyo.Var(m.Arcs, m.Times, within = pyo.Reals)
    return m

######################### STATIONS ########################################
###########################################################################

def STATIONS_vars(m):
    m.compressor_P = pyo.Var(m.Stations, m.Times, within = pyo.NonNegativeReals)
    # beta lb for ipopt log
    # ! SAKSHI --> bounds beta
    m.compressor_beta = pyo.Var(m.Stations, m.Times, bounds = (1.05, 2), within = pyo.NonNegativeReals)
    # ! SAKSHI --> eta fixed
    m.compressor_eta = pyo.Var(m.Stations, m.Times, bounds = (0, 1), within = pyo.NonNegativeReals)
    m.compressor_eta.fix(0.8)
    return m

######################### PIPES ###########################################
###########################################################################

# PIPES
def PIPE_vars(m, scale):
    # finite volumes --> variables in the middle of the pipes (at boundaries, pressure = node_p, mass flow = inlet_w/outlet_w)
    m.interm_w = pyo.Var(
        m.Pipes_VolExtrC_interm, m.Times, within = pyo.Reals) 
    # ! SAKSHI --> pressure bounds
    p_min, p_max = 30e5, 120e5
    m.interm_p = pyo.Var(
        m.Pipes_VolExtrR_interm, m.Times, bounds = (p_min/scale['p'], p_max/scale['p']), within = pyo.NonNegativeReals) 
    # friction    
    m.u2 = pyo.Var(m.Pipes_VolExtrC, m.Times, within = pyo.Reals)
    m.u = pyo.Var(m.Pipes_VolExtrC, m.Times, within = pyo.Reals) 
    # density
    # ! SAKSHI --> density bounds
    rho_min, rho_max = 30, 80
    m.pipe_rho = pyo.Var(m.Pipes_VolExtrR, m.Times, bounds = (rho_min, rho_max), within = pyo.NonNegativeReals)   
    # consumption variables --> nodes and pipes
    wcons_keys = list(m.Pipes_VolCenterC.data()) + [(n, 0) for n in m.Nodes.data() if n not in m.NodesSources.data()]
    m.wCons = pyo.Var(wcons_keys, m.Times, within = pyo.Reals)  
    return m       


######################### DUALS VARIABLES ################################
###########################################################################
def DUALS_ipopt_vars(m):
    # Ipopt bound multipliers (IMPORT)
    m.ipopt_zL_out = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    m.ipopt_zU_out = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    # Ipopt bound multipliers (EXPORT)
    m.ipopt_zL_in = pyo.Suffix(direction=pyo.Suffix.EXPORT)
    m.ipopt_zU_in = pyo.Suffix(direction=pyo.Suffix.EXPORT)
    # Ipopt constraint dual (IMPORT/EXPORT)
    m.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT)
    return m

