# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 15:44:41 2024

@author: ssnaik
"""

import os
import pytest
from gas_net.util.import_data import import_data_from_excel
from gas_net.modelling_library.SETS import (NODE_sets, 
                                            ARC_sets, 
                                            STATION_set,
                                            PIPE_sets
                                            )
import pyomo.environ as pyo

class TestGaslibParser:
    def test_sets_build(self):
       
        self.network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_11\\networkData.xlsx'
        self.input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_11\\inputData.xlsx'
        
        # import data
        self.networkData, self.inputData = import_data_from_excel(self.network_data_path, self.input_data_path)
        
        #Make model
        m = pyo.ConcreteModel()
        
        #Make node sets
        NODE_sets(m, self.networkData)
        assert len(m.Nodes) == 11
        
        #Make arc sets
        ARC_sets(m, self.networkData)
        assert len(m.Arcs) == 10
        
        #Make station set
        STATION_set(m, self.networkData)
        assert len(m.Stations) == 2
        
        #Make pipe set
        PIPE_sets(m, self.networkData)
        assert len(m.Pipes) == 8
     
        
        
if __name__ == "__main__":
    pytest.main()
