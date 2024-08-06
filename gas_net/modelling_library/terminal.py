# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 12:33:01 2024

@author: ssnaik
"""
import pyomo.environ as pyo
def terminal_constraints(m, w_terminal, p_terminal):
    def terminal_flow(m, p, vol):
        tf = m.Times.last()
        return m.interm_w[p, vol, tf] >= w_terminal
    m.terminal_flow = pyo.Constraint(m.Pipes_VolExtrC)
    
    def terminal_pressure(m, p , vol):
        tf = m.Times.last()
        return m.interm_p[p, vol, tf] >= p_terminal
    m.terminal_pressure = pyo.Constraint(m.Pipes_VolExtrC)
    return m

def collect_css_data(m, solved_dynamic_model, current_time):
    """This function collects flow and pressure data from the solution of th edynamic model
       This is the cyclic steady state soluton that'll be used for writing terminal constraints
    """
    
    m.css_flows = pyo.Param(m.Pipes_VolExtrC_interm, initialize = 0, mutable=True)
    m.css_pressures = pyo.Param(m.Pipes_VolExtrR_interm, initialize = 0, mutable = True)
    
    for p, vol in m.Pipes_VolExtrC_interm:
        m.css_flows[p, vol] = pyo.value(solved_dynamic_model.interm_w[p, vol, current_time])
            
    for p, vol in m.Pipes_VolExtrR_interm:
        m.css_pressures[p, vol] = pyo.value(solved_dynamic_model.interm_p[p, vol, current_time])
            
def css_terminal_constraints(m):
    m.terminal_flow_slacks_p = pyo.Var(m.Pipes_VolExtrC_interm, domain=pyo.NonNegativeReals)
    m.terminal_flow_slacks_n = pyo.Var(m.Pipes_VolExtrC_interm, domain=pyo.NonPositiveReals)
    m.terminal_pressure_slacks_p = pyo.Var(m.Pipes_VolExtrR_interm, domain=pyo.NonNegativeReals)
    m.terminal_pressure_slacks_n = pyo.Var(m.Pipes_VolExtrR_interm, domain=pyo.NonPositiveReals)
    
    def _terminal_flow(m, p, vol):
        tf = m.Times.last()
        t0 = m.Times.first()
        return m.interm_w[p, vol, tf] == m.interm_w[p, vol, t0] + m.terminal_flow_slacks_p[p,vol] + m.terminal_flow_slacks_n[p,vol]
    m.terminal_flow = pyo.Constraint(m.Pipes_VolExtrC_interm, rule = _terminal_flow)
    
    def _terminal_pressure(m, p , vol):
        tf = m.Times.last()
        t0 = m.Times.first()
        return m.interm_p[p, vol, tf] ==m.interm_p[p, vol, t0]+ m.terminal_pressure_slacks_p[p,vol] + m.terminal_pressure_slacks_n[p,vol]
    m.terminal_pressure = pyo.Constraint(m.Pipes_VolExtrR_interm, rule = _terminal_pressure)
    return m