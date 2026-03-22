# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 11:09:12 2025

@author: ssnaik
"""

from gas_net.examples.MPC.cyclic_steady_state.kai_small_experiment.run_nmpc_multistage_multiple_params_kai_small import make_plant_and_controller_model
import os

def make_controller_model(input_data_path,
                          network_data_path, 
                          options_data_path,
                          horizon, 
                          num_time_periods):
    
    #Demand uncertainty is the first uncertain parameter
    demand_uncertainty_min = {(0, 7): 0, (7, 13): -5, 
                              (13, 31): 0, (31, 37): -5, 
                              (37, 55): 0, (55, 61): -5,
                              (61, 79): 0, (79, 85): -5,
                              (85, 103): 0, (103, 109): -5,
                              (109,127): 0, (127, 133): -5,
                              (133, 145): 0}
    
    demand_uncertainty_nom = None
    
    demand_uncertainty_max = {(0, 7): 0, (7, 13): 5, 
                              (13, 31): 0, (31, 37): 5, 
                              (37, 55): 0, (55, 61): 5,
                              (61, 79): 0, (79, 85): 5,
                              (85, 103): 0, (103, 109): 5,
                              (109,127): 0, (127, 133): 5,
                              (133, 145): 0}
    
    #Supply pressure uncertainty is the second uncertain parameter
    source_pressure_uncertainty_min = 0.85
    source_pressure_uncertainty_nom = 1
    source_pressure_uncertainty_max = 1.15
    
    #Optimal cyclic steady state files
    ocss_path = r"C:\Users\ssnaik\Biegler\gas_networks_italy\gas_networks\gas_net\ocss_multiple_params_kai_small"
    
    ocss_min_min = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_min_min_scenario.xlsx")
    ocss_min_nom = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_min_nom_scenario.xlsx")
    ocss_min_max = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_min_max_scenario.xlsx")
    
    ocss_nom_min = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_nom_min_scenario.xlsx")
    ocss_nom_nom = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_nom_nom_scenario.xlsx")
    ocss_nom_max = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_nom_max_scenario.xlsx")
    
    ocss_max_min = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_max_min_scenario.xlsx")
    ocss_max_nom = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_max_nom_scenario.xlsx")
    ocss_max_max = os.path.join(ocss_path, "optimal_css_24hrs_kai_small_max_max_scenario.xlsx")
    
    #Make controller models 
    #Min demand scenario
    controller_min_min, m_plant = make_plant_and_controller_model(ocss_min_min,
                                                                  input_data_path,
                                                                  network_data_path, 
                                                                  options_data_path,
                                                                  horizon, 
                                                                  num_time_periods,
                                                                  uncertainty = demand_uncertainty_min, 
                                                                  source_pressure_uncertainty_factor=source_pressure_uncertainty_min)
    
    controller_min_nom, _ = make_plant_and_controller_model(ocss_min_nom,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_min, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_nom)
    
    controller_min_max, _ = make_plant_and_controller_model(ocss_min_max,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_min, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_max)
    
    #Nominal demand scenario
    controller_nom_min, _ = make_plant_and_controller_model(ocss_nom_min,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_nom, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_min)
    
    controller_nom_nom, _ = make_plant_and_controller_model(ocss_nom_nom,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_nom, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_nom)
    
    controller_nom_max, _ = make_plant_and_controller_model(ocss_nom_max,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_nom, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_max)
    
    #Max demand scenario
    controller_max_min, _ = make_plant_and_controller_model(ocss_max_min,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_max, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_min)
    
    controller_max_nom, _ = make_plant_and_controller_model(ocss_max_nom,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_max, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_nom)
    
    controller_max_max, _ = make_plant_and_controller_model(ocss_max_max,
                                                            input_data_path,
                                                            network_data_path, 
                                                            options_data_path,
                                                            horizon, 
                                                            num_time_periods,
                                                            uncertainty = demand_uncertainty_max, 
                                                            source_pressure_uncertainty_factor=source_pressure_uncertainty_max)
    
    return controller_min_min, controller_min_nom, controller_min_max, controller_nom_min, controller_nom_nom, controller_nom_max, controller_max_min, controller_max_nom, controller_max_max, m_plant
    
    