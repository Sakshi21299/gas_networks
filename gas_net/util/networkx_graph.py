# -*- coding: utf-8 -*-
"""
Created on Mon Jan 17 13:07:21 2022

@author: Lavinia
"""

# Importing all the libraries used

import networkx as nx
import matplotlib.pyplot as pl

#==============================================================================
""" CREATE GRAPH """
#==============================================================================

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
    keys = pos.keys()
    for key in keys:
        x, y = pos[key]
        pos_labels[key] = (x+offset_x, y+offset_y)
        labels[key] = G.nodes[key]['name']
    return pos_labels, labels

def graph_plot(G, node_labels=False):
    
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
        pos_labels, labels = offset_labels(G, pos, offset_x = 0, offset_y = 0.03)
        nx.draw_networkx_labels(G, pos=pos_labels, labels=labels)

    pl.axis('off')
   
    return 

def plot_graph_with_layout(G, node_labels=False):
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
    layout = nx.kamada_kawai_layout(G)
    
    pos_labels, labels = offset_labels(G, pos=layout)
    node_colors, node_types = colorcode_nodes(labels)
    nx.draw_networkx(G, pos=layout, 
            edge_color = edge_colors, 
            linewidths = 4,
            with_labels = False,
            node_size = node_sizes,
            node_color=[node_colors[node_types[node]] for node in G.nodes()])
    
    # Adjust label positions by adding the offset to the x-coordinate
    label_positions = {node: (x + 0.05, y-0.05) for node, (x, y) in layout.items()}

    
    nx.draw_networkx_labels(G, pos=label_positions, labels={node: f'{label}\n' for node, label in labels.items()},
                        font_size=7, font_color='black')

    return 

def colorcode_nodes(labels):
    # Define node colors based on node types
    node_colors = {'source': 'blue', 'sink': 'lightgreen', 'bypass': 'yellow'}

    # Extract node types from labels and assign colors accordingly
    node_types = {}
    for node, label in labels.items():
        if label.startswith('sink'):
            node_types[node] = 'sink'
        elif label.startswith('source'):
            node_types[node] = 'source'
        elif label.startswith('innode'):
            node_types[node] = 'bypass'
    return node_colors, node_types

