# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 13:56:00 2024

@author: ssnaik
"""
import numpy as np
import matplotlib.pyplot as plt
import pyomo.environ as pyo

def dynamic_demand_profile(ss_demand, num_time_periods = 1, epsilon = 0):
    #amplitude = 1/20 #Original amplitude set for all results
    amplitude = 1/20
    
    time_length = len(ss_demand)
    x = np.linspace(0, 2* num_time_periods*np.pi, time_length)
    dynamic_demand = ss_demand + ss_demand*np.sin(x)*amplitude + epsilon*np.sin(x)*amplitude

    return dynamic_demand

def dynamic_demand_profile_extended(dynamic_demand):
    dynamic_demand1 = dynamic_demand
    dynamic_demand2 = dynamic_demand[1:]
    
    dynamic_demand_extended = np.concatenate((dynamic_demand1, dynamic_demand2))
    return dynamic_demand_extended
    
    
def dynamic_demand_calculation(m, num_time_periods = 1, time_length = None, extended_profile = False, epsilon = 0):
    if time_length is None:
        time_length = len(m.Times)
        
    dynamic_demand = {}
    for s in m.wCons:
        if s[0].startswith('sink'):
            ss_demand = [pyo.value(m.wCons[s])]*time_length
            dynamic_demand[s[0]] = dynamic_demand_profile(ss_demand,  num_time_periods, epsilon = epsilon)
            if extended_profile:
                dynamic_demand[s[0]] = dynamic_demand_profile_extended(dynamic_demand[s[0]])
    return dynamic_demand

def uncertain_demand_calculation(m, dynamic_demand, uncertainty={(0,13): -0.1, (13, 25): -0.1}):
    uncertain_demand = {}
    for s in m.wCons:
        if s[0].startswith('sink'):
            uncertain_demand_list = []
            for keys in uncertainty.keys():
                dyn_demand = dynamic_demand[s[0]][keys[0]:keys[1]]
                ss_demand = dynamic_demand[s[0]][0]
                uncertain_demand_profile =  dyn_demand + (dyn_demand - ss_demand)*uncertainty[keys]
                uncertain_demand_list.append(uncertain_demand_profile)
            uncertain_demand[s[0]] = np.concatenate(uncertain_demand_list)
    return uncertain_demand
                
         
if __name__ == "__main__":
    ss_demand = [16.35417]*72
    dynamic_demand = dynamic_demand_profile(ss_demand,num_time_periods = 3, epsilon = 0)
    print(dynamic_demand)
    plt.plot(dynamic_demand)
    # dynamic_demand = dynamic_demand_profile(ss_demand, num_time_periods=3, epsilon = 1)
    # plt.plot(dynamic_demand)
    # plt.plot(ss_demand)
    
    #Extended demand profile
    plt.figure()
    dynamic_demand_extended = dynamic_demand_profile_extended(dynamic_demand)
    plt.plot(dynamic_demand_extended)
    plt.xlabel('Time(hrs)')
    plt.ylabel('Gas demand at each node (kg/s)')
    #plt.plot(ss_demand)