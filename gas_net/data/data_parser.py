import json
import os
import pandas as pd
import numpy as np 
from pathlib import Path

class DataParserGaslib:
    def __init__(self, folder ="data_files\GasLib_11", 
                 file_names = ["network.json", "nominations.json", "params.json", "slack_nodes.json"]):
        self.folder = folder
        self.file_names = file_names
        self.current_path = os.getcwd()
        self.folder_path = os.path.join(self.current_path, self.folder)
        self.excel_file_path_network = os.path.join(self.folder_path, "networkData.xlsx")
        self.all_link_names = []
        
    def _write_to_excel(self, excel_file_path, new_sheet_name, column_names, new_data):
        # Check if the file exists
        if Path(excel_file_path).is_file():
            # Load existing Excel file
            xls = pd.ExcelFile(excel_file_path)
        
            # Create a DataFrame from the new data
            new_df = pd.DataFrame(new_data, columns = column_names)
        
        
            # Append the new DataFrame to the existing Excel file
            with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode = 'a') as writer:
                new_df.to_excel(writer, sheet_name=new_sheet_name, index=False, header=True)
        
            print(f'Data appended to {excel_file_path}, sheet: {new_sheet_name}')
        
        else:
            # Create a new Excel file if it doesn't exist
            new_df = pd.DataFrame(new_data, columns = column_names)
        
            # Write the new DataFrame to the new Excel file
            new_df.to_excel(excel_file_path, sheet_name = new_sheet_name, index=False, header=True)
        
            print(f'New Excel file created at {excel_file_path}')
     
    def _read_node_data(self, data):
        new_sheet_name = "Nodes"
        column_names =['', 'source', 'pMin', 'pMax', 'height', 'lat', 'long']
        dt = []
        for key in data.keys():
            dt.append([data[key]['name'], 
                       data[key]['name'] if data[key]['name'].startswith('entry') else np.NaN, 
                       data[key]['min_pressure'],
                       data[key]['max_pressure'],
                       data[key]['elevation'],
                       data[key]['x_coord'],
                       data[key]['y_coord']])
        self._write_to_excel(self.excel_file_path_network, new_sheet_name, column_names, dt)
    #Nvol	Direction	uMax	MMgas	Tgas	xCH4	Z

    def _read_pipe_data(self, data):
        new_sheet_name = "Pipes"
        column_names = ['', 'length', 'A', 'omega', 'diameter', 'roughness', 'Nvol', 
                        'Direction', 'uMax', 'MMgas', 'Tgas', 'xCH4', 'Z']
        dt = []
        for key in data.keys():
            diameter = data[key]['diameter']
            area = np.pi*diameter**2/4
            perimeter = np.pi*diameter
            dt.append([data[key]['name'],
                      data[key]['length'],
                      area,
                      perimeter,
                      diameter,
                      data[key]['roughness'],
                      int(2),
                      np.NaN,
                      np.NaN,
                      np.NaN,
                      np.NaN,
                      np.NaN,
                      np.NaN
                ])
            
            self.all_link_names.append(data[key]['name'])
        self._write_to_excel(self.excel_file_path_network, new_sheet_name, column_names, dt)
        
    def _read_arc_data(self):
        new_sheet_name = "Arcs"
        column_names = ['', 'nodeIN', 'nodeOUT']
        dt = []
        for name in self.all_link_names:
            node_in = name.split('_')[1]
            node_out = name.split('_')[2]
            dt.append([name,
                       node_in,
                       node_out
                ])
            
        self._write_to_excel(self.excel_file_path_network, new_sheet_name, column_names, dt)
    
    def _read_compressor_data(self, data):
        new_sheet_name = "Stations"
        column_names = ['', 'pInMax', 'pInMin', 'pOutMax', 'max_power']
        dt = []
        for key in data.keys():
            dt.append([data[key]['name'],
                       np.NaN,
                       data[key]['min_inlet_pressure'],
                       data[key]['max_outlet_pressure'],
                       data[key]['max_power']
                ])
            self.all_link_names.append(data[key]['name'])
        self._write_to_excel(self.excel_file_path_network, new_sheet_name, column_names, dt) 
            
    
    def read_data(self):
        for name in self.file_names:
            file_path = os.path.join(self.folder_path, name)
            
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
    
            if name == "network.json":
                for key in data.keys():
                    if key == 'nodes':
                       self._read_node_data(data[key])
                    elif key == 'pipes':
                        self._read_pipe_data(data[key])
                    elif key == 'compressors':
                        self._read_compressor_data(data[key])
                   
                self._read_arc_data()
            #Not reading this data yet
            #Need to generate input data since gaslib has steady state consumption
            if name == "nominations.json":
                print(data)
            if name == 'params.json':
                print(data)
            if name == "slack_nodes.json":
                print(data)
 

if __name__ =="__main__":
    dataparser = DataParserGaslib()
    dataparser.read_data()