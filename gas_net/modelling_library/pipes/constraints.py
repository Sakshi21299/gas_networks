# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 10:49:55 2021

@author: Lavinia
"""

import pyomo.environ as pyo
from gas_net.modelling_library.pipes.functions import Pipe_MassFlow, Pipe_GasDensity, Pipe_DerMass, Pipe_Pressure

# PIPE: MASS CONSTRAINTS
#==============================================================================

def PIPE_mass_constr(
        m, scale, dt, method = 'BACKWARD'):
    
    ## assert: options ###
    assert(method in ['BACKWARD', 'FORWARD'])

    ############## dynamic mass balance #########################  
    def PIPE_mass_balance_rule(
            m, p, vol, t): # 1-->N-1 

        # skip first time step   
        if t == m.Times.first():
            return pyo.Constraint.Skip
        else:
            V = m.Area[p]*m.Length[p]
            N = m.Nvol[p]    
            
            ############ left hand side #################
            # LHS: derivative term (between t and t_prev)                         
            dMdt = Pipe_DerMass(
                m, p, vol, t, N, V, scale, dt)                

            ############## right hand side #############
            # RHS: define timestep depending on differentiation method
            t_RHS = m.Times.prev(t) if method=="FORWARD" else t           
            # RHS: mass flow rates
            w = Pipe_MassFlow(m, p, vol, t_RHS, N)
            w_next = Pipe_MassFlow(m, p, vol+1, t_RHS, N) # next finite volume
            # RHS: consumption
            cons = m.wCons[p, vol, t_RHS]
    
            ############## constraint #########################              
            return dMdt == (w*scale["w"] - w_next*scale["w"] - cons*scale["w"])
        m.PIPE_mass_balance = pyo.Constraint(
            m.Pipes_VolCenterC, m.Times, 
            rule = PIPE_mass_balance_rule)
    return m 


# PIPE: MOMENTUM CONSTRAINTS
#==============================================================================

def PIPE_momentum_constr(
        m, scale, networkData):
    
    Nodes = networkData['Nodes']

    ############ fun : friction ###################
    def friction_term(m, p, vol, t):
        # volume length    
        N = m.Nvol[p]
        start = 1
        end = m.Nvol[p]  + 1
        l = m.Length[p] / (N-1)  
        # first and last volume --> L/2
        if vol == start or (vol+1) == end: 
            l = l/2                                   
        # rho friction     
        rhoFrict = m.pipe_rho[p, vol, t] # variable 
        # u squared
        u2 = m.u2[p, vol, t]
        # parameters
        A = m.Area[p]
        rough = m.Roughness[p]        
        D = m.Diam[p] 
        cf = (-4*pyo.log10(rough/(3.71 * D))) ** (-2)
        omega = m.Omega[p]
        # final term
        coeffU2 = cf/2 * rhoFrict * (omega * l / A) * (scale["u2"]/scale["p"])
        return u2 * coeffU2 

    ############ fun : geodetic ###################
    def geodetic_term(m, p, vol, t):      
        # find geodetic term  
        N = m.Nvol[p]
        start = 1
        end = N+1
        n_in = m.Arcs_NodeIN[p]
        n_out = m.Arcs_NodeOUT[p]  
        dz = (Nodes[n_out]["height"]-Nodes[n_in]["height"])/(N-1)
        # first and last volume RCR --> R/2
        if vol == start or (vol+1) == end: # R/2
            dz = dz/2
        # geodetic head
        if int(dz) < 1:
            geodetic = 0     
        else: 
            rhoGeo = m.pipe_rho[p, vol, t]
            geodetic = rhoGeo * 9.81 * dz / scale["p"] 
        return geodetic  
    
    #################### constraint ###################
    def PIPE_momentum_balance_rule(m, p, vol, t): # 1-->N     
        N = m.Nvol[p]       
        end = N + 1
        if vol == end: # skip if last volume
            return pyo.Constraint.Skip
        else:            
            # LHS
            press = Pipe_Pressure(m, p, vol, t, N)
            press_next = Pipe_Pressure(m, p, vol+1, t, N) # next finite volume
            # RHS
            friction = friction_term(m, p, vol, t)
            geodetic = geodetic_term(m, p, vol, t)                          
            return 100 * (press - press_next) == (friction + geodetic) * 100
    m.PIPE_momentum_balance = pyo.Constraint(
        m.Pipes_VolExtrR,
        m.Times, rule = PIPE_momentum_balance_rule)

    return m


def PIPE_nlp_auxiliary_constr( m, scale):
    # gas speed
    def PIPE_nonlinear_speed_rule(m, p, vol, t): 
        # flow
        w = Pipe_MassFlow(m, p, vol, t, m.Nvol[p])
        # density
        rho = m.pipe_rho[p, vol, t]
        A = m.Area[p]
        return m.u[p, vol, t] * rho == (w * scale["w"] / A)
    m.PIPE_nonlinear_speed = pyo.Constraint(
        m.Pipes_VolExtrC, m.Times, 
        rule = PIPE_nonlinear_speed_rule)

    # gas density
    def PIPE_nonlinear_rho_rule(m, p, vol, t): 
        # gas density (equation of state)
        N = m.Nvol[p]
        rhoCalc = Pipe_GasDensity(m, scale, p, vol, t, N, calc = True) 
        return m.pipe_rho[p, vol, t] == rhoCalc
    m.PIPE_nonlinear_rho = pyo.Constraint(
        m.Pipes_VolExtrR, m.Times, 
        rule = PIPE_nonlinear_rho_rule)
    
    return m


def PIPE_flow_reversal_constr(m, scale):
    # smoothing flow reversal term
    eps = m.eps
    def PIPE_nonlinear_friction_smooth_rule(m, p, vol, t): 
        u = m.u[p, vol, t]
        abs_u = pyo.sqrt(u**2 + eps)
        return m.u2[p, vol, t] == (u * abs_u) / scale["u2"]
    m.PIPE_nonlinear_friction_smooth = pyo.Constraint(
        m.Pipes_VolExtrC, m.Times, 
        rule = PIPE_nonlinear_friction_smooth_rule)
    
    return m
