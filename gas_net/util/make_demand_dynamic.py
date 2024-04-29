# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 13:56:00 2024

@author: ssnaik
"""
import numpy as np
import matplotlib.pyplot as plt
import pyomo.environ as pyo

def dynamic_demand_profile(ss_demand, epsilon = 0):
    time_length = len(ss_demand)
    x = np.linspace(0, 2*np.pi, time_length)
    dynamic_demand = ss_demand + ss_demand*np.sin(x)/20 + epsilon*np.sin(x)/20
    return dynamic_demand

def dynamic_demand_profile_extended(dynamic_demand):
    dynamic_demand1 = dynamic_demand
    dynamic_demand2 = dynamic_demand[1:]
    
    dynamic_demand_extended = np.concatenate((dynamic_demand1, dynamic_demand2))
    return dynamic_demand_extended
    
    
def dynamic_demand_calculation(m, time_length = None, extended_profile = False, epsilon = 0):
    if time_length is None:
        time_length = len(m.Times)
        
    dynamic_demand = {}
    for s in m.wCons:
        if s[0].startswith('sink'):
            ss_demand = [pyo.value(m.wCons[s])]*time_length
            dynamic_demand[s[0]] = dynamic_demand_profile(ss_demand, epsilon = epsilon)
            if extended_profile:
                dynamic_demand[s[0]] = dynamic_demand_profile_extended(dynamic_demand[s[0]])
    return dynamic_demand


            
if __name__ == "__main__":
    ss_demand = [16]*25
    dynamic_demand = dynamic_demand_profile(ss_demand, epsilon = 0)
    plt.plot(dynamic_demand)
    dynamic_demand = dynamic_demand_profile(ss_demand, epsilon = 1)
    plt.plot(dynamic_demand)
    plt.plot(ss_demand)
    
    #Extended demand profile
    plt.figure()
    ss_demand = [16]*50
    dynamic_demand_extended = dynamic_demand_profile_extended(dynamic_demand)
    plt.plot(dynamic_demand_extended)
    plt.plot(ss_demand)