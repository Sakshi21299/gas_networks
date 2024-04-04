# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 16:41:25 2024

@author: ssnaik
"""
import matplotlib.pyplot as plt
import pyomo.environ as pyo
def plot_compressor_beta(m):
    plt.figure()
    compressor_beta = {}
    for c in m.Stations:
        beta = []
        for t in m.Times:
            beta.append(pyo.value(m.compressor_beta[c, t]))
        compressor_beta[c] = beta
        plt.plot(beta, label = c)
    plt.xlabel("Time (hrs)")
    plt.ylabel("Compressor beta (Pout/Pin)")
    plt.legend()
    
def plot_compressor_power(m):
    plt.figure()
    compressor_power = {}
    for c in m.Stations:
        power = []
        for t in m.Times:
            power.append(pyo.value(m.compressor_P[c, t]))
        compressor_power[c] = power
        plt.plot(power, label = c)
    plt.xlabel("Time (hrs)")
    plt.ylabel("Compressor Power (kWh)")
    plt.legend()
        
        
    