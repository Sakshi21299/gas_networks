import pyomo.environ as pyo
import pyomo.dae as dae

#==============================================================================
""" VARIABLES """
#==============================================================================

######################### NETWORK ###########################################
###########################################################################

def NODE_vars(m, wSourceFree = False):
    # NODES
    m.node_p = pyo.Var(m.Nodes, m.Times, within = pyo.NonNegativeReals)
    #if wSourceFree: 
    # nmpc
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
    m.generalDistance = pyo.Var(m.Stations, m.Times, within = pyo.Reals)
    m.Tamb = pyo.Var(m.Stations, m.Times, within = pyo.NonNegativeReals)
    #m.Tamb = pyo.Param(m.Stations, m.Times, default=288.15, mutable=True, within = pyo.NonNegativeReals)
    return m

######################### PIPES ###########################################
###########################################################################

# PIPES
def PIPE_finite_volume_vars(
        m, ContinuousSet=False, wConsFree = False):
    m.interm_w = pyo.Var(
        m.Pipes_VolExtrC_interm, m.Times, within = pyo.Reals) # 2/N-1 (+ inlet_w, outlet_w) (estremi C)
    m.interm_p = pyo.Var(
        m.Pipes_VolExtrR_interm, m.Times, within = pyo.NonNegativeReals) # 2/N (+ inlet_p, outlet_p) (estremi R) 
    # consumption variables
    # if wConsFree: # nmpc
    wcons_keys = list(m.Pipes_VolCenterC.data()) + [(n, 0) for n in m.Nodes.data() if n not in m.NodesSources.data()]
    m.wCons = pyo.Var(wcons_keys, m.Times, within = pyo.Reals)
    
    if ContinuousSet:
        m.M = pyo.Var(m.Pipes_VolCenterC, m.Times, within = pyo.NonNegativeReals) # 1/N-1 (centro C)        
        m.dMdt = dae.DerivativeVar(m.M, wrt = m.Times) # --> for now it is defined over mass      
    return m

def PIPE_nlp_friction_vars(m):     
    m.u2 = pyo.Var(m.Pipes_VolExtrC, m.Times, within = pyo.Reals)
    m.u = pyo.Var(m.Pipes_VolExtrC, m.Times, within = pyo.Reals) 
    m.pipe_rho = pyo.Var(m.Pipes_VolExtrR, m.Times, within = pyo.NonNegativeReals)   
    return m       


def PIPE_nlp_fix_vars(m, TimesSet):
    m.yD = pyo.Var(
        m.Pipes_VolExtrC_UndirPWL, TimesSet['yD'], within = pyo.Binary)
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

