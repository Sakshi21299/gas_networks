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
                                            PIPE_sets,
                                            PIPE_finite_volumes_sets)
import pyomo.environ as pyo

class TestGaslibParser:
    def test_sets_build(self):
       
        self.network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_11\\networkData.xlsx'
        input_data_path = self.network_data_path
        
        #We don't need input data to make sets
        #I will update this test once I know what should go in the input data file
        input_data_path = []
        
        # import data
        networkData = import_data_from_excel(self.network_data_path, input_data_path)
        
        #Make model
        m = pyo.ConcreteModel()
        
        #Make node sets
        NODE_sets(m, networkData)
        assert len(m.Nodes) == 11
        
        #Make arc sets
        ARC_sets(m, networkData)
        assert len(m.Arcs) == 10
        
        #Make station set
        STATION_set(m, networkData)
        assert len(m.Stations) == 2
        
        #Make pipe set
        PIPE_sets(m, networkData)
        assert len(m.Pipes) == 8
        
        
        #Pipe finite volume sets
        PIPE_finite_volumes_sets(m, networkData)
        #What would be the thing to test while building this set? Not sure 
        
if __name__ == "__main__":
    pytest.main()
