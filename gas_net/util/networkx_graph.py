# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 13:07:21 2022

@author: Lavinia
"""

# Importing all the libraries used

import networkx as nx
import matplotlib.pyplot as pl
from matplotlib.lines import Line2D
#==============================================================================
""" CREATE GRAPH """
#==============================================================================
TRANSPARENT = True
FONTSIZE = 10
AXESOFF = True
LINEWIDTH = 4.0

pl.rcParams["font.size"] = FONTSIZE
pl.rcParams["text.usetex"] = True
def set_elem_attr(G, elem, attr, isedge = True):
    """ Set attributes to an elemet of a graph """
    for a in attr.keys():
        if isedge:
            G.edges[elem][a] = attr[a] 
        else:
            G.nodes[elem][a] = attr[a]  
    return G

def graph_construction(networkData):
    
    """ 
    Build (and plot) graph from network dictionary.
    
    """
    
    #Declaration of the network graph
    G = nx.Graph()
        
    Arcs = networkData["Arcs"]
    Valves = networkData["Valves"]
    Pipes = networkData["Pipes"]
    Nodes = networkData["Nodes"]    
    Stations = networkData["Stations"]    

    # create dictionary of nodes elements
    n_elems = {}
    for elem, node in enumerate(sorted(Nodes.keys())):
        n_elems[node]=elem
            
    # build graph
    for node in Nodes.keys():
        elem = n_elems[node]
        G.add_node(elem, name=node)
        G = set_elem_attr(G, elem, Nodes[node], isedge = False)   
    
    for arc in Arcs.keys():       
        row = Arcs[arc]
        n_in = n_elems[row["nodeIN"]]
        n_out = n_elems[row["nodeOUT"]]
        if arc in Pipes.keys():
            category = "pipe"
        elif arc in Valves.keys():
            category = "valve"
        elif arc in Stations.keys():
            category = "compressor station"
        G.add_edge(n_in, n_out, array_origin = n_in, category=category)
        
        # set attributes
        elem = (n_in, n_out)
        G.edges[elem]["name"] = arc
        G = set_elem_attr(G, elem, Arcs[arc])

    return G


#==============================================================================
""" PLOT GRAPH """
#==============================================================================

def offset_labels(G, pos, offset_x = 0.1,offset_y=0):
    pos_labels = {}
    labels = {}
    labels_to_plot = {}
    keys = pos.keys()
    for key in keys:
        x, y = pos[key]
        pos_labels[key] = (x+offset_x, y+offset_y)
        labels[key] = G.nodes[key]['name']
        if G.nodes[key]['name'].startswith('source'):
            labels_to_plot[key] = 'S' + G.nodes[key]['name'].split('_', 1)[1]
        if G.nodes[key]['name'].startswith('sink'):
            labels_to_plot[key] = 'D' + G.nodes[key]['name'].split('_', 1)[1]
        if G.nodes[key]['name'].startswith('innode'):
            labels_to_plot[key] = 'N' + G.nodes[key]['name'].split('_', 1)[1]
         
    return pos_labels, labels, labels_to_plot

def graph_plot(G, node_labels=False, edge_labels = False):
    
    ## set positions
    ref_node =list(G.nodes)[0]
    pos = {n : [G.nodes[n]["long"], G.nodes[n]["lat"]] for n in G.nodes}

    ## set figure
    fig = pl.figure()        

    ## draw
    # edge_colors
    edge_colors = []
    widths = []
    for a in G.edges:
        # set color
        color = 'tab:green'
        if 'category' in G.edges[a].keys():
            if G.edges[a]["category"] == "pipe": 
                color = "black"
                width = 0.5
            elif "valve" in G.edges[a]["category"]: 
                color = "pink"
                width = 4
            elif G.edges[a]["category"] == "compressor station": 
                color = "red"  
                width = 4
            else:
                color = "black"
                width = 0.5                  
        edge_colors.append(color)
        widths.append(width)
    
    # node colors
    node_colors = ["tab:blue" for n in G.nodes]
    node_sizes = [5 for n in G.nodes]    
    nx.draw_networkx(G, pos=pos, 
            edge_color = edge_colors, 
            node_color = node_colors,
            linewidths = 4,
            with_labels = False,
            node_size = node_sizes)

    # nodes labels
    if node_labels:
        pos_labels, labels, labels_to_plot = offset_labels(G, pos, offset_x = 0, offset_y = 0.05)
        nx.draw_networkx_labels(G, pos=pos_labels, labels=labels_to_plot)

    return 

def plot_graph_with_layout(G, node_labels=False, edge_labels = False):
    ## draw
    # edge_colors
    edge_colors = []
    widths = []
    edge_labels = {}
    for a in G.edges:
        # set color
        color = 'tab:green'
        if 'category' in G.edges[a].keys():
            if G.edges[a]["category"] == "pipe": 
                color = "black"
                width = 0.5
                edge_labels[a] = ''
            elif "valve" in G.edges[a]["category"]: 
                color = "pink"
                width = 4
                edge_labels[a] = ''
            elif G.edges[a]["category"] == "compressor station": 
                color = "red"  
                width = 4
                edge_labels[a] = ''
            else:
                color = "black"
                width = 0.5  
                edge_labels[a] = ''
            edge_labels[(3, 39)] = 'C4'
            edge_labels[(1, 18)] = 'C3'
            edge_labels[(5, 25)] = 'C1'
            edge_labels[(30, 7)] = 'C6'
            edge_labels[(38, 6)] = 'C5'
            edge_labels[(0, 10)] = 'C2'
        edge_colors.append(color)
        widths.append(width)
    
    
    # node colors
    node_colors = ["tab:blue" for n in G.nodes]
    node_sizes = [5 for n in G.nodes]
    layout = nx.kamada_kawai_layout(G)
    
    pos_labels, labels, labels_to_plot = offset_labels(G, pos=layout)
    node_colors, node_types = colorcode_nodes(labels)
    
    pl.figure()
    nx.draw_networkx(G, pos=layout, 
            edge_color = edge_colors, 
            linewidths = 4,
            with_labels = False,
            node_size = node_sizes,
            node_color=[node_colors[node_types[node]] for node in G.nodes()])
    
    # Adjust label positions by adding the offset to the x-coordinate
    label_positions = get_label_positions(layout, labels)

    if node_labels:
        nx.draw_networkx_labels(G, pos=label_positions, labels={node: f'{label}\n' for node, label in labels_to_plot.items()},
                            font_size=7, font_color='black')
    
    if edge_labels:
        edge_label_positions = {node: (x + 0.05, y-0.03) for node, (x, y) in layout.items()}
    
        edge_label_positions[3] = (layout[3][0] - 0.07, layout[3][1] + 0.15) #C4
        edge_label_positions[1] = (layout[1][0] - 0.07, layout[1][1] + 0.15) #C3
        edge_label_positions[5] = (layout[5][0] + 0.06, layout[5][1] + 0.1) #C1
        edge_label_positions[0] = (layout[0][0] - 0.17, layout[0][1] + 0.05) # C2
        edge_label_positions[38] = (layout[38][0] - 0.18, layout[38][1] + 0.05) #C5
        edge_label_positions[30] = (layout[30][0] - 0.08, layout[30][1] + 0.17) #C6
        
        
        
        nx.draw_networkx_edge_labels(G, pos = edge_label_positions, edge_labels=edge_labels, font_color='red', font_size=7, rotate=False)
   
    node_legend_items = [Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=7, label='$\mathrm{Sources (S)}$'),
                         Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=7, label='$\mathrm{Sinks (D)}$'),
                         Line2D([0], [0], marker='o', color='w', markerfacecolor='yellow', markersize=7, label='$\mathrm{Connecting \: nodes (N)}$'),
                         Line2D([0], [0], color='r', markersize=7, label='$\mathrm{Compressor \: lines (C)}$'),
                         Line2D([0], [0], color='k', markersize=7, label='$\mathrm{Pipes}$')]
    
    # Add legend to the plot
    pl.legend(handles=node_legend_items, loc='upper right')
    pl.axis("off")

    pl.savefig("gaslib40_schematic.pdf")
    return 

def get_label_positions(layout, labels):
    label_positions = {}
    for node, (x,y) in layout.items():
        #Default label position
        label_positions[node] = (x + 0.05, y-0.03)
        node_name = labels[node]
        
        #Change label position if its not good
        if node_name.startswith('source'):
            label_positions[node] = (x - 0.05, y-0.06)
        if node_name.startswith('sink') or node_name =='innode_2' or node_name == 'innode_6':
            label_positions[node] = (x + 0.03, y+0.03)
        if node_name == 'sink_2' or node_name == 'sink_3':
            label_positions[node] = (x - 0.04, y+0.02)
        if node_name == 'innode_5':
            label_positions[node] = (x - 0.03, y+0.03)
        if node_name == 'innode_4' or node_name == 'innode_3':
            label_positions[node] = (x + 0.01, y-0.1)
        if node_name == 'sink_11' or node_name == 'innode_1' or node_name == 'innode_7' or node_name =='sink_15' or node_name == 'sink_4':
            label_positions[node] = (x + 0.07, y - 0.03)
        if node_name =='sink_10' or node_name =='innode_8' or node_name == 'sink_26' or node_name == 'sink_6':
            label_positions[node] = (x - 0.01, y - 0.1)
        if node_name=='sink_23' or node_name =='sink_29':
            label_positions[node] = (x - 0.08, y-0.05)
        if node_name =='sink_25':
            label_positions[node] = (x - 0.08, y)
        if node_name == 'sink_19':
            label_positions[node] = (x, y - 0.1)
        if node_name == 'sink_20':
            label_positions[node] = (x, y + 0.05)
    return label_positions

def colorcode_nodes(labels):
    # Define node colors based on node types
    node_colors = {'source': 'blue', 'sink': 'green', 'bypass': 'yellow', 'other':'lightpink'}

    # Extract node types from labels and assign colors accordingly
    node_types = {}
    for node, label in labels.items():
        if label.startswith('sink') or label.startswith('exit'):
            node_types[node] = 'sink'
        elif label.startswith('source') or label.startswith('entry'):
            node_types[node] = 'source'
        elif label.startswith('innode'):
            node_types[node] = 'bypass'
        else:
            node_types[node] = 'other'
    return node_colors, node_types

if __name__ == "__main__":
    from gas_net.util.import_data import import_data_from_excel
    network_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\networkData.xlsx'
    input_data_path = r'C:\\Users\\ssnaik\\Biegler\\gas_networks_italy\\gas_networks\\gas_net\\data\\data_files\\Gaslib_40\\inputData.xlsx'

    #Load network and input data
    networkData, inputData = import_data_from_excel(network_data_path, input_data_path)
    G = graph_construction(networkData)
    plot_graph_with_layout(G, node_labels=True, edge_labels = True)
