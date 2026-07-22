# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:51:58 2024

@author: ssnaik
"""

import pyomo.environ as pyo
import numpy as np


def apply_stability_constraint(m_controller):
    #Define tracking cost 
    m_controller.lyapunov_function_current = pyo.Var(initialize = 1)
    m_controller.lyapunov_function_prev = pyo.Param(initialize = 1, mutable = True)
    m_controller.tracking_cost_plant_prev = pyo.Param(initialize= 1, mutable = True)
    m_controller.delta = pyo.Param(initialize = 0.1)
    def _lyapunov_function_definition(m):
        return m.lyapunov_function_current == (sum((m.interm_p[p, vol, t] - m.interm_p_ocss[p, vol, t])**2 
                                                   for p, vol in m.Pipes_VolExtrR_interm for t in m.Times if t != m.Times.last()) 
                                               + sum((m.compressor_P[s, t] - m.compressor_P_ocss[s, t])**2
                                                     for s in m.Stations for t in m.Times if t != m.Times.last())
                                               )
    m_controller.lyapunov_function_definition = pyo.Constraint(rule = _lyapunov_function_definition)
        
    def _stability_constraint(m):
        return m.lyapunov_function_current <= m.lyapunov_function_prev - m.delta*m.tracking_cost_plant_prev
    m_controller.stability_constraint = pyo.Constraint(rule = _stability_constraint)
    
def apply_stability_constraint_infhor(m_controller):
    #Define tracking cost 
    m_controller.finite.lyapunov_function_current = pyo.Var(initialize = 1)
    m_controller.infinite.lyapunov_function_eachpt = pyo.Var(m_controller.infinite.Times, initialize = 1)
    m_controller.infinite.lyapunov_function_current = pyo.Var(initialize = 1)
    
    m_controller.lyapunov_function_prev = pyo.Param(initialize = 1, mutable = True)
    m_controller.tracking_cost_plant_prev = pyo.Param(initialize= 1, mutable = True)
    m_controller.delta = pyo.Param(initialize = 0.1)
    
    def _lyapunov_function_definition_finite(m):
        return m.finite.lyapunov_function_current== 1/1000*(sum((m.finite.pipe_rho[p, vol, t] - m.finite.pipe_rho_ocss[p, vol, t])**2 
                                                          for p, vol in m.finite.Pipes_VolExtrR 
                                                          for t in m.finite.Times if t != m.finite.Times.last()
                                                          )
                                                      )
    m_controller.lyapunov_function_definition_finite = pyo.Constraint(rule = _lyapunov_function_definition_finite)
    
    # For cyclic steady state, it is necessary to determine the correct ocss point in the infinite horizon to 
    # calculate the lyapunov function
    def  _lyapunov_function_definition_infinite_eachpt(m, tau):
        if tau == 1:
            return pyo.Constraint.Skip
        
        # First need to convert tau to t 
        delta_t = 3600
        t_bar = m.finite.Times.last()
        gamma = pyo.value(m.infinite.gamma)
        t = t_bar + 1/gamma*np.arctanh(tau)*delta_t 
        t_nearest = min(m.finite.Times, key=lambda x: abs(x - t/t_bar))

        return  m.infinite.lyapunov_function_eachpt[tau] == sum((m.infinite.pipe_rho[p, vol, tau] - m.finite.pipe_rho_ocss[p, vol, t_nearest])**2 
                                                          for p, vol in m.infinite.Pipes_VolExtrR)
    m_controller.lyapunov_function_definition_eachpt = pyo.Constraint(m_controller.infinite.Times, rule = _lyapunov_function_definition_infinite_eachpt)
    
    #This is the actual lyapunov function definition for the infinite horizon
    def _lyapunov_function_definition_infinite(m):
        return m.infinite.lyapunov_function_current == 1/1000*(sum(m.infinite.lyapunov_function_eachpt[tau]
                                              for tau in m.infinite.Times if tau != m.infinite.Times.last())
                                              )
    m_controller.lyapunov_function_definition_infinite = pyo.Constraint(rule = _lyapunov_function_definition_infinite)
    
    # This is the actual stability cinstraint on the full controller
    def _stability_constraint(m):
        return m.finite.lyapunov_function_current + m.finite.lyapunov_function_current <= m.lyapunov_function_prev - 1/1000*m.delta*m.tracking_cost_plant_prev
    m_controller.stability_constraint = pyo.Constraint(rule = _stability_constraint)
    
if __name__ == "__main__":
    from gas_net.examples.run_nlp_gaslib40 import run_model
    import pyomo.contrib.mpc as mpc
    _, m_controller = run_model()
    
    

    controller_interface = mpc.DynamicModelInterface(m_controller, m_controller.Times)
    
    #See if this shifts the steady state by 1
    #It does!
    controller_interface.shift_values_by_time(1)
    
    #Rewrite the controller 0 values at the last time point
    
    [m_controller.compressor_beta_ocss[s, 24.0].fix(m_controller.compressor_beta_ocss[s, 0.0]) for s in m_controller.Stations]
    [m_controller.interm_p_ocss[p, vol, 24.0].fix(m_controller.interm_p_ocss[p, vol, 0.0]) for p, vol in m_controller.Pipes_VolExtrR_interm]
    
    