# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 12:33:01 2024

@author: ssnaik
"""
import pyomo.environ as pyo
import pandas as pd

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

def load_css(m_controller, ocss_file_path):
    df = pd.read_excel(ocss_file_path, sheet_name=None, index_col="Unnamed: 0")
    cycle_length = 6
    m_controller.interm_p_ocss = pyo.Var(m_controller.Pipes_VolExtrR_interm, m_controller.Times)
    for p, vol in m_controller.Pipes_VolExtrR_interm:
        column_name = "interm_p['" + str(p) + "', " + str(vol) +", :]" 
        for t in m_controller.Times:
            t_inp = t%cycle_length
            m_controller.interm_p_ocss[p, vol, t].fix(df['interm_p'][column_name][t_inp])
            
    # m_controller.pipe_rho_ocss = pyo.Var(m_controller.Pipes_VolExtrR, m_controller.Times)
    # for p, vol in m_controller.Pipes_VolExtrR:
    #     column_name = "pipe_rho['" + str(p) + "', " + str(vol) +", :]" 
    #     for t in m_controller.Times:
    #         t_inp = t%cycle_length
    #         m_controller.pipe_rho_ocss[p, vol, t].fix(df['pipe_rho'][column_name][t_inp])
    
    m_controller.compressor_beta_ocss = pyo.Var(m_controller.Stations, m_controller.Times)
    for s in m_controller.Stations:
        column_name = "compressor_beta['" + str(s) + "', :]"
        for t in m_controller.Times:
            t_inp = t%cycle_length
            m_controller.compressor_beta_ocss[s, t] = df['compressor beta'][column_name][t_inp]
            
    m_controller.compressor_P_ocss = pyo.Var(m_controller.Stations, m_controller.Times)
    for s in m_controller.Stations:
        column_name = "compressor_P['" + str(s) + "', :]"
        for t in m_controller.Times:
            t_inp = t%cycle_length
            m_controller.compressor_P_ocss[s, t] = df['compressor power'][column_name][t_inp]
            
    m_controller.wSource_ocss = pyo.Var(m_controller.NodesSources, m_controller.Times)
    for s in m_controller.NodesSources:
        column_name = "wSource['" + str(s) + "', :]"
        for t in m_controller.Times:
            t_inp = t%cycle_length
            m_controller.wSource_ocss[s, t] = df['wSource'][column_name][t_inp]
            
    m_controller.pSource_ocss = pyo.Var(m_controller.NodesSources, m_controller.Times)
    for s in m_controller.NodesSources:
        column_name = "pSource['" + str(s) + "', :]"
        for t in m_controller.Times:
            t_inp = t%cycle_length
            m_controller.pSource_ocss[s, t] = df['pSource'][column_name][t_inp]


    m_controller.compressor_beta_ocss.fix()
    m_controller.compressor_P_ocss.fix()
    m_controller.interm_p_ocss.fix()
    m_controller.wSource_ocss.fix()
    m_controller.pSource_ocss.fix()
            
def css_terminal_constraints(m, num_time_periods = 1, horizon = 24):    
    
    N = num_time_periods
    K = int(horizon/N)
  
    def _terminal_controls(m, c):
        tf = N*K
        t0 = (N-1)*K
        return m.compressor_P[c, tf] == m.compressor_P[c, t0] 
    m.terminal_controls_constraint = pyo.Constraint(m.Stations, rule = _terminal_controls)
    
    # def _terminal_controls_css(m, c):
    #     t0 = (N-1)*K
    #     return m.compressor_P[c, t0] == m.compressor_P_ocss[c, t0]
    # m.terminal_controls_css = pyo.Constraint(m.Stations, rule = _terminal_controls_css)
     
    def _terminal_pressure(m, p , vol):
        tf = N*K
        t0 = (N-1)*K
        return m.interm_p[p, vol, tf] ==m.interm_p[p, vol, t0]
        
    m.terminal_pressure = pyo.Constraint(m.Pipes_VolExtrR_interm, rule = _terminal_pressure)
    
    # def _terminal_source_pressure(m, s):
    #     tf = N*K
    #     t0 = (N-1)*K
    #     return m.pSource['source_3', tf] ==m.pSource['source_3', t0]
    # m.terminal_source_pressure = pyo.Constraint(rule = _terminal_source_pressure)
    
    # def _terminal_pressure_css(m, p , vol):
    #     t0 = (N-1)*K
    #     return m.interm_p[p, vol, t0] ==m.interm_p_ocss[p, vol, t0]
        
    # m.terminal_pressure_css = pyo.Constraint(m.Pipes_VolExtrR_interm, rule = _terminal_pressure_css)
    
    
    # def _terminal_supply_flows_css(m, s):
    #     t0 = (N-1)*K
    #     return m.wSource[s, t0] == m.wSource_ocss[s, t0]
    # m.terminal_supply_flow_css = pyo.Constraint(m.NodesSources, rule = _terminal_supply_flows_css)
    
    # def _terminal_supply_flow(m, s):
    #     tf = N*K
    #     t0 = (N-1)*K
    #     return m.wSource[s, tf] == m.wSource[s, t0]
    # m.terminal_supply_flow = pyo.Constraint(m.NodesSources, rule = _terminal_supply_flow)
    
    return m

def css_terminal_constraints_each_point(m, num_time_periods = 1, horizon = 6, ocss_file_path= None):
    #We need the CSS here since it is used to write the terminal constraints at all times 
    #in the last period
    load_css(m, ocss_file_path)
    
    N = num_time_periods
    K = int(horizon/N)
    m.last_period = pyo.Set(initialize = [t for t in m.Times if t >= (N-1)*K and t <= N*K])

    def _terminal_pipe_rho(m, p , vol):
        return m.pipe_rho[p, vol, (N-1)*K] ==m.pipe_rho_ocss[p, vol, 0]
        
    m.terminal_pipe_rho = pyo.Constraint(m.Pipes_VolExtrR_interm, rule = _terminal_pipe_rho)
    
    def _terminal_controls(m, c, t):
        return m.compressor_P_ocss[c, t] == m.compressor_P[c, t]        
    m.terminal_controls_constraint = pyo.Constraint(m.Stations, m.last_period, rule = _terminal_controls)
    
    
    # def _terminal_supply_flow(m, p, vol, t):
    #     return m.interm_p_ocss[p, vol, t] == m.interm_p[p, vol, t]
    # m.terminal_supply_flow = pyo.Constraint(m.Pipes_VolExtrR_interm, m.last_period, rule = _terminal_supply_flow)
    return m 
    
def css_terminal_last_point(m, horizon = 6, ocss_file_path = None):
    load_css(m, ocss_file_path)
    m.terminal_p_slack = pyo.Var(m.Pipes_VolExtrR_interm, initialize = 0, domain = pyo.Reals)
    #m.terminal_rho_slack = pyo.Var(m.Pipes_VolExtrR, initialize = 0, domain = pyo.Reals)
    m.terminal_power_slack = pyo.Var(m.Stations, initialize = 0, domain = pyo.Reals)
    
    # def _terminal_pipe_rho(m, p , vol):
    #     return m.pipe_rho[p, vol, horizon] == m.pipe_rho_ocss[p, vol, 0] + m.terminal_rho_slack[p, vol]
    # m.terminal_pipe_rho = pyo.Constraint(m.Pipes_VolExtrR, rule = _terminal_pipe_rho)
    
    def _terminal_pressure(m, p , vol):
        return m.interm_p[p, vol, horizon] == m.interm_p_ocss[p, vol, 0] + m.terminal_p_slack[p, vol]
        
    m.terminal_pressure = pyo.Constraint(m.Pipes_VolExtrR_interm, rule = _terminal_pressure)  

    
    def _terminal_comp_power_css(m, s):
        return m.compressor_P[s, horizon] == m.compressor_P_ocss[s, 0] + m.terminal_power_slack[s]
    m.terminal_supply_flow_css = pyo.Constraint(m.Stations, rule = _terminal_comp_power_css)
    return m