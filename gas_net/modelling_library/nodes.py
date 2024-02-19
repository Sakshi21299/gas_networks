
import math
import pyomo.environ as pyo
        
#==============================================================================
""" CONSTRAINTS - NODE """
#==============================================================================

############################ SIMPLE NODES #####################################
###############################################################################

def NODE_constr(m, scale, networkData):
    Nodes = networkData["Nodes"]
    
    ###### PRESSURE #####
    # nodes
    for n in m.Nodes:
        if n not in m.NodesSources:
            pMax = Nodes[n]["pMax"]/scale["p"]
            pMin = Nodes[n]["pMin"]/scale["p"]
            for t in m.Times:
                # bounds
                m.node_p[n, t].setlb(pMin)
                m.node_p[n, t].setub(pMax)
            
    ###### MASS  balance #####
    def NODE_mass_balance_rule(m, n, t): 
        IN = sum(m.outlet_w[arc, t] for arc in m.Nodes_ArcsIN[n])
        OUT = sum(m.inlet_w[arc, t] for arc in m.Nodes_ArcsOUT[n])
        cons = m.wCons[n, 0, t]
        return IN == OUT + cons
    m.NODE_mass_balance = pyo.Constraint(
        m.Nodes - m.NodesSources, m.Times, 
        rule = NODE_mass_balance_rule)
    
    return m


################ SOURCE NODES #################################################
###############################################################################

def NODE_SOURCE_constr(m):

    ################# PRESSURE CONSTRAINTS ######################
   
    def NODE_SOURCE_pressure_rule(m, n, t):               
        return m.node_p[n,t] == m.pSource[n, t]
    m.NODE_SOURCE_pressure = pyo.Constraint(
        m.NodesSources, m.Times, 
        rule = NODE_SOURCE_pressure_rule)
    
    ################# MASS BALANCE CONSTRAINTS ######################
    def NODE_SOURCE_mass_balance_rule(m, n, t): 
        ## mass flow from arcs ##
        IN = sum(m.outlet_w[arc, t] for arc in m.Nodes_ArcsIN[n])
        OUT = sum(m.inlet_w[arc, t] for arc in m.Nodes_ArcsOUT[n])    
        injection = m.wSource[n, t]
        return IN + injection == OUT
    m.NODE_SOURCE_mass_balance = pyo.Constraint(
        m.NodesSources, m.Times, 
        rule = NODE_SOURCE_mass_balance_rule)
    return m
