#!/usr/bin/env python
# coding: utf-8

# In[36]:


import json
from networkx.readwrite import json_graph

def read_graph_from_json(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return json_graph.adjacency_graph(data)


json_file_path = r'C:\Users\mohal\Downloads\districting_data_extracted\districting-data-2020-county\ID_county.json'
graph = read_graph_from_json(json_file_path)


print(graph.nodes)  


# In[35]:


import json
from networkx.readwrite import json_graph

def read_graph_from_json(json_file):
    with open(json_file) as f:
        data = json.load(f)
    return json_graph.adjacency_graph(data)


filepath = r'C:\Users\mohal\Downloads\districting_data_extracted\districting-data-2020-county\\'  
filename = 'ID_county.json'


G = read_graph_from_json(filepath + filename)


for node in G.nodes:
    G.nodes[node]['TOTPOP'] = G.nodes[node]['P0010001']  
    G.nodes[node]['C_X'] = G.nodes[node]['INTPTLON20']  
    G.nodes[node]['C_Y'] = G.nodes[node]['INTPTLAT20']  


print(G.nodes[0]) 


# In[38]:


from geopy.distance import geodesic


dist = { (i, j): 0 for i in G.nodes for j in G.nodes }


for i in G.nodes:
    for j in G.nodes:
        
        loc_i = (G.nodes[i]['C_Y'], G.nodes[i]['C_X'])
        loc_j = (G.nodes[j]['C_Y'], G.nodes[j]['C_X'])  
        
        
        dist[i, j] = geodesic(loc_i, loc_j).miles  


print(f"Distance between node 0 and node 1: {dist[0, 1]} miles")


# In[40]:


import math


deviation = 0.01


k = 2


total_population = sum(G.nodes[node]['TOTPOP'] for node in G.nodes)


L = math.ceil((1 - deviation / 2) * total_population / k)
U = math.floor((1 + deviation / 2) * total_population / k)


print("Using L =", L, "and U =", U, "and k =", k)


# In[44]:


import gurobipy as gp
from gurobipy import GRB

 
m = gp.Model()


x = m.addVars( G.nodes, G.nodes, vtype=GRB.BINARY )


# In[45]:


m.setObjective( gp.quicksum( dist[i,j] * dist[i,j] * G.nodes[i]['TOTPOP'] * x[i,j] for i in G.nodes for j in G.nodes ), GRB.MINIMIZE )


# In[51]:


m.addConstrs( gp.quicksum( x[i,j] for j in G.nodes ) == 1 for i in G.nodes )


m.addConstr( gp.quicksum( x[j,j] for j in G.nodes ) == k )


m.addConstrs( gp.quicksum( G.nodes[i]['TOTPOP'] * x[i,j] for i in G.nodes ) >= L * x[j,j] for j in G.nodes )
m.addConstrs( gp.quicksum( G.nodes[i]['TOTPOP'] * x[i,j] for i in G.nodes ) <= U * x[j,j] for j in G.nodes )


m.addConstrs( x[i,j] <= x[j,j] for i in G.nodes for j in G.nodes )

m.update()


# In[56]:


import networkx as nx
DG = nx.DiGraph(G)


f = m.addVars( DG.edges, G.nodes ) 


m.addConstrs( gp.quicksum( f[u,i,j] - f[i,u,j] for u in G.neighbors(i) ) == x[i,j] for i in G.nodes for j in G.nodes if i != j )


M = G.number_of_nodes() - 1
m.addConstrs( gp.quicksum( f[u,i,j] for u in G.neighbors(i) ) <= M * x[i,j] for i in G.nodes for j in G.nodes if i != j )


m.addConstrs( gp.quicksum( f[u,j,j] for u in G.neighbors(j) ) == 0 for j in G.nodes )

m.update()


# In[57]:


m.Params.MIPGap = 0.0

m.optimize()


# In[59]:


print(m.objVal)



centers = [ j for j in G.nodes if x[j,j].x > 0.5 ]

districts = [ [ i for i in G.nodes if x[i,j].x > 0.5 ] for j in centers ]
district_counties = [ [ G.nodes[i]["NAME20"] for i in districts[j] ] for j in range(k)]
district_populations = [ sum(G.nodes[i]["TOTPOP"] for i in districts[j]) for j in range(k) ]


for j in range(k):
    print("District",j,"has population",district_populations[j],"and contains counties",district_counties[j])
    print("")


# In[60]:


import geopandas as gpd


filepath = r'C:\Users\mohal\Downloads\districting_data_extracted\districting-data-2020-county\\'  
filename = 'ID_county.shp'  


df = gpd.read_file(filepath + filename)


print(df.head())


# In[62]:


assignment = [ -1 for i in G.nodes ]

labeling = { i : -1 for i in G.nodes }
for j in range(k):
    district = districts[j]
    for i in district:
        labeling[i] = j


node_with_this_geoid = { G.nodes[i]['GEOID20'] : i for i in G.nodes }


for u in range(G.number_of_nodes()):
    
    geoid = df['GEOID20'][u]
    
    
    i = node_with_this_geoid[geoid]
    
    
    
    assignment[u] = labeling[i]
    

df['assignment'] = assignment

my_fig = df.plot(column='assignment').get_figure()

