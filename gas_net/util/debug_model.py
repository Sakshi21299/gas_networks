# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 11:27:11 2024

@author: ssnaik
"""
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.core.util.model_diagnostics import (DiagnosticsToolbox)
from pyomo.contrib.incidence_analysis import IncidenceGraphInterface
import pyomo.environ as pyo
def debug_gas_model(model):
    
    #Fix degrees of freedom to make the problem square
    for s in model.Stations:
        for t in model.Times:
            model.compressor_beta[s, t].fix()
    print("degrees_of_freedom = ", degrees_of_freedom(model))
    #assert degrees_of_freedom(model) == 0
    dt = DiagnosticsToolbox(model)
    dt.report_structural_issues()
    
    #Unfix degrees of freedom
    for s in model.Stations:
        for t in model.Times:
            model.compressor_beta[s, t].fix()
    
    ipopt = pyo.SolverFactory('ipopt')
    ipopt.solve(model, tee=True)
    
    dt = DiagnosticsToolbox(model)
    dt.report_numerical_issues()
    dt.display_variables_at_or_outside_bounds()
    dt.display_underconstrained_set()
    dt.display_overconstrained_set()
    dt.display_constraints_with_large_residuals()
   
def analyze_violations(model):
    # Analyze constraint violations
    violated_constraints = []
    for constr in model.component_data_objects(pyo.Constraint, active=True):
        constr_value = pyo.value(constr)
        if constr_value > 10:  # Constraint is violated
            violated_constraints.append((constr.name, constr_value))
    
    # Sort the violated constraints by the degree of violation
    violated_constraints.sort(key=lambda x: x[1], reverse=True)
    
    # Print the most violated constraints
    print("Most violated constraints:")
    for name, value in violated_constraints[:]:  # Display top 5 violated constraints
        print(f"{name}: {value}")
        
    # Analyze variable bound violations
    violated_variable_bounds = []
    for var in model.component_data_objects(pyo.Var):
        if var.has_lb():
            if pyo.value(var) < var.lb:
                violation_amount = var.lb - pyo.value(var)
                violated_variable_bounds.append((var.name, "Lower bound", violation_amount))
        if var.has_ub():
            if pyo.value(var) > var.ub:
                violation_amount = pyo.value(var) - var.ub
                violated_variable_bounds.append((var.name, "Upper bound", violation_amount))
    
    # Sort the violated variable bounds by the degree of violation
    violated_variable_bounds.sort(key=lambda x: x[2], reverse=True)
    
    # Print the most violated variable bounds
    print("Most violated variable bounds:")
    for name, bound_type, violation_amount in violated_variable_bounds[:5]:  # Display top 5 violated variable bounds
        print(f"{name}: {bound_type} violated by {violation_amount}")
     
    
    