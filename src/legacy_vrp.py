import networkx as nx
import matplotlib.pyplot as plt
from random import randint, uniform
import math
import os
from collections import deque
import copy
from datetime import datetime

######################################################################################################
##########################################     Classes:     ##########################################
##########################################                  ##########################################

#####################  Driver()  #####################
#####################            #####################

class Driver:
    
    def __init__(driver, G, driver_label, time_limit):   

        if time_limit is None:
            time_limit = float('inf')

        driver.label = driver_label
        driver.hot = False
        driver.time, driver.sched, driver.graph = create_driver_cycle(G, driver_label)

        if driver.time is not None:
            if driver.time > time_limit:
                #print(f"<<<::: INITIALIZING HOT DRIVER {driver_label}, driver.time = {driver.time}, driver.sched = {driver.sched} :::>>>")
                driver.hot = True
            elif driver.time == float('inf'):
                #print(f"<<<::: INITIALIZING LOST DRIVER {driver_label}, driver.time = {driver.time}, driver.sched = {driver.sched} :::>>>")
                driver.hot = True

#####################  Drivers()  #####################
#####################             #####################

class Drivers:
    
    def __init__(drivers, G=None, driver_labels=None, H=None, res_type=None, time_limit=None, wp=True):        

        if time_limit is None:
            time_limit = float('inf')
        drivers.time_limit = time_limit

        if G is None:
            G = nx.DiGraph()
            G.add_node( 0, pos=(0,0), driver=None, time=None )
            H = nx.DiGraph()
            H.add_node(0)
            H.add_node(-1)
            drivers.G = G
            
        else:    
            drivers.G = G.copy()
            
        if driver_labels == None: # Initialize a new driver object.
            drivers.labels = set(out_neigh(0, G))
            drivers.fired_list = []
            if wp:
                print(f"Start a new Drivers with time_limit = {drivers.time_limit}, using labels = {drivers.labels}. (fired_list = {drivers.fired_list})")
        else:
            drivers.labels = driver_labels
            if wp:
                print(f"Updating Drivers, time_limit = {drivers.time_limit} using labels = {driver_list}. (fired_list = {drivers.fired_list})")

        drivers.initialize_G()
        
        if H is None:
            drivers.H = initialize_residual_H(drivers.G, type=res_type)
            if wp:
                print(f"Started a new Drivers completed. Now initializing H, of type {res_type}, from the list of drivers {drivers.labels}.")
            
            
        else:
            drivers.H = H

    #####################  initialize_G()  #####################
    #####################                  #####################
    
    def initialize_G(drivers):
            
            drivers.max_time = 0
            drivers.min_time = float('inf')
            
            drivers.graphs = {}
            drivers.sched = {}
            drivers.time = {}
            drivers.drivers = {}
            drivers.hot_drivers = {}

            #for driver_label in drivers.labels:
                
                #if driver_label not in set(out_neigh(0, drivers.G)):
                    #print(f"Driver {driver_label}, has been Fired (or lost). Number of Drivers: {set(out_neigh(0, drivers.G))}")
                    

            #for driver_label in set(out_neigh(0, drivers.G)):
                
                #if driver_label not in drivers.labels:
                    #print(f"Driver {driver_label}, has been Hired! Number of Drivers: {set(out_neigh(0, drivers.G))}")

            drivers.labels = set(out_neigh(0, drivers.G))
        
            for driver_label in drivers.labels:
                
                driver = Driver(drivers.G, driver_label, drivers.time_limit)
                
                if driver.time is None:
                    drivers.fired_list.append(driver_label)
                    print(f"Driver {driver_label}, has been fired AGAIN??? (or lost). Number of Drivers Left: {len(drivers.labels) - len(drivers.fired_list)}")
   
                else:
                    if driver.hot is True:
                        drivers.hot_drivers[driver_label] = driver.time

                    driver.graph.nodes[0]['time'] = None
                    driver.graph.nodes[0]['driver'] = None
                    drivers.G = nx.compose(drivers.G, driver.graph)
                    drivers.graphs[driver.label] = driver.graph
                    drivers.sched[driver.label] = driver.sched
                    drivers.time[driver.label] = driver.time
                    drivers.drivers[driver.label] = driver
                    
                    if driver.time > drivers.max_time:              
                        drivers.max_time = driver.time
                        
                    #if driver.time > drivers.time_limit:
                        #if driver.hot is False:
                            #print(f"<<<::: ERROR :::>>> : this driver {driver_label} is hot, but somehow not labeled as hot = True, driver.hot = {driver.hot}")
                            #driver.hot = True
                        #drivers.hot_drivers[driver_label] = driver.time
                        
                    if driver.time < drivers.min_time:              
                        drivers.min_time = driver.time

            for driver_label in drivers.fired_list:
                drivers.labels.remove(driver_label)
                
            drivers.fired_list = []
        
            if len(drivers.labels) != 0:
                drivers.ave_time = sum([t for t in drivers.time.values()])/len(drivers.labels)
            else:
                drivers.ave_time = 0

    #####################   update()   #####################
    #####################              #####################

    def update(drivers, driver_labels=None):

        if driver_labels is None:
            
            drivers.initialize_G()

        else:

            print(f"updating effected drivers = {driver_labels}")
            S = set()
            
            for driver_label in driver_labels:
                for x in drivers.sched[driver_label]:
                    S.add(x)
                    
            drivers.G.removed_nodes_from(S)
            
            for driver_label in driver_labels:
                
                new_driver.time, new_driver.sched, new_driver.graph = create_driver_cycle(G, driver_label)
                new_driver = Driver(drivers.G, driver_label)
                
                if new_driver.time is None:
                    print(f"Driver {driver_label}, has been fired.")
                    drivers.fired_list.append(driver_label)
                else:
                    drivers.G = nx.compose(drivers.G, new_driver.graph)
                    drivers.graphs[new_driver.label] = new_driver.graph
                    drivers.sched[new_driver.label] = new_driver.sched
                    drivers.time[new_driver.label] = new_driver.time
                    drivers.drivers[new_driver.label] = new_driver

            drivers.max_time = 0
            drivers.min_time = float('inf')
            
            for driver_label, driver in drivers.drivers.items():
                
                if driver.time > drivers.max_time:              
                    drivers.max_time = driver.time
                if driver.time > drivers.time_limit:
                    drivers.hot_drivers[driver_label] = driver.time
                if driver.time < drivers.min_time:              
                    drivers.min_time = driver.time

            for driver_label in drivers.fired_list:
                drivers.labels.remove(driver_label)
                drivers.graphs.pop(driver_label)
                drivers.sched.pop(driver_label)
                drivers.time.pop(driver_label)
                drivers.drivers.pop(driver_label)
                drivers.hot_drivers.pop(driver_label)
                
            drivers.fired_list = []
        
            if len(drivers.labels) != 0:
                drivers.ave_time = sum([t for t in drivers.time.values()])/len(drivers.labels)
            else:
                drivers.ave_time = 0
                
######################################################################################################
##########################################     Methods:     ##########################################
##########################################                  ##########################################

#####################  date_sign()  #####################
#####################               #####################

def date_sign(str=None):

    if str is None:
        str = 'Casey Moffatt'
        
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()

    # Print name.
    print(f"\nAuthor: {str}")
    
    # Print date and time.
    print("Current Date: ", current_date)
    print("Current Time: ", current_time)
    print("\n")

    return current_datetime
    
#####################    length()   #####################
#####################               #####################

def length(iter):

    if iter is None:
        return None

    else:
        return len(iter)

#####################  out_neigh()  #####################
#####################               #####################

def out_neigh(v, G):

    arr = list(G.successors(v))
    #print("out-neigh of v = {} in G(v) = {}".format(v,arr))
    return(arr)

#####################  in_neigh()  #####################
#####################              #####################

def in_neigh(v, G):

    arr = list(G.predecessors(v))
    #print("in-neigh of v = {} in G(v) = {}".format(v,arr))
    return(arr)

#####################  child()  #####################
#####################           #####################

def child(v, G):

    out_neigh = list(G.successors(v))
    if len(out_neigh) >= 1:
        child = out_neigh[0]
    else:
        child = None

    return(child)

#####################  parent()  #####################
#####################            #####################

def parent(v, G):

    in_neigh = list(G.predecessors(v))
    if len(in_neigh) >= 1:
        parent = in_neigh[0]
    else:
        parent = None

    return(parent)

##################### generate_load() #####################
#####################                 #####################

def generate_load(max_dist, wp=True):

    while True:        
        pickup = (uniform(-6, 6), uniform(-6, 6))
        dropoff = (uniform(-6, 6), uniform(-6, 6))  
        load_dist = math.dist((0, 0), pickup) + math.dist(pickup, dropoff) + math.dist(dropoff, (0, 0))
        if load_dist  <= max_dist:
            if wp:
                #print(f"leg 1 = {math.dist((0, 0), pickup)}")
                #print(f"leg 2 = {math.dist(pickup, dropoff)}")
                #print(f"leg 3 = {math.dist(dropoff, (0, 0))}")
                print(f"load created, total distance = {load_dist}")
            return pickup, dropoff

##################### create_truck_problem() #####################
#####################                        #####################

def create_truck_problem(num_loads, max_dist, file_index=None, wp=True):

    if file_index:
        file_index = str(file_index)
    else:
        file_index = ''
   
    loads = []   
    file_name = "Generated_Problems/loads" + file_index + "_" + str(num_loads) + "_" + str(max_dist) + ".txt" # Name of the file
    
    for _ in range(num_loads):
        pickup, dropoff = generate_load(max_dist, wp=wp)
        loads.append(f"({pickup[0]}, {pickup[1]}), ({dropoff[0]}, {dropoff[1]})")     
    
    with open(file_name, "w") as file:   
        file.write("\n".join(loads))

    # Get the current directory and create the file path
    current_directory = os.getcwd()  # Get the current working directory
    file_path = os.path.join(current_directory, file_name)  # Construct the full file path
    if wp:
        print(f"current path = {file_path}")

    return file_path

##################### create_graph_from_file() #####################
#####################                          #####################

def create_graph_from_file(file_path):
    
    # Create an empty graph
    A = []
    B = []
    labels = {(0,0): 0}
    Dist = {(0,0): 0}
    G = nx.DiGraph()
    G.add_node(0, pos=(0, 0))
    i = -1
    
    # Read the file and process each line
    with open(file_path, 'r') as file:
        for line in file:

            i += 2
            # Remove any surrounding whitespace
            line = line.strip()
            
            # Split the line into pickup and dropoff coordinates
            pickup, dropoff = line.split('), (')
            
            # Remove surrounding parentheses and split into x and y coordinates
            pickup = tuple(map(float, pickup.replace('(', '').split(',')))
            dropoff = tuple(map(float, dropoff.replace(')', '').split(',')))
            
            G.add_node(i, pos=(pickup[0], pickup[1]), time=None, driver=None)  #Create nodes with positions, None for time, and None for driver. 
            G.add_node(i + 1, pos=(dropoff[0], dropoff[1]), time=None, driver=None)
            # Add an edge between the pickup and dropoff points
            G.add_edge(i, i + 1, weight=math.dist(pickup, dropoff), time=math.dist(pickup, dropoff) )
            G.add_edge(0, i, weight=math.dist((0, 0), pickup)+250, time=math.dist((0, 0), pickup) )
            G.add_edge(i + 1, 0, weight=math.dist(dropoff, (0, 0))+250, time=math.dist(dropoff, (0, 0)) )

    return G

##################### create_residual_H() #####################
#####################                     #####################

def initialize_residual_H(G, type=None):

    if type is None:
        type = 'stan' # Standard residual graph vs. duplicatation of the wearehouse node (aka modified residual).
        print(f"type={type}: Defaulting to type='stan', use type='mod' if duplication of wearhouse is desired.")

    n = len(G.nodes)
    H = nx.DiGraph()
    H.add_node(0, pos=( -2, (n-1)//2 ))
    if type == 'mod':
        H.add_node(-1, pos=( 2, (n-1)//2 ))
    A = range( 1, n-1, 2 )
    B = range( 2, n, 2 )
    que_1 = deque(A)
    que_2 = deque(B)

    while que_1 or que_2:

        v = que_1.popleft()
        y = G.nodes[v]['pos']
        
        u = que_2.popleft()
        x = G.nodes[u]['pos']

        H.add_node(v, pos=(-1, v))
        H.add_node(u, pos=(1, v))

        
        for w in A:
            
            if w != v:                      # This keeps us from adding edges at loads (cannot be deleted in G).
                z = G.nodes[w]['pos']
                H.add_edge(u, w, time=math.dist(x, z), weight=math.dist(x, z))

        if type == "mod":
            H.add_edge(-1, u, time=-math.dist( (0,0), x ), weight=-math.dist( (0,0), x ) - 250 )
            H.add_edge(v, 0, time=-math.dist( y, (0,0) ) , weight=-math.dist( y, (0,0) ) - 250 )
        if type == "stan":
            H.add_edge(0, u, time=-math.dist( (0,0), x ), weight=-math.dist( (0,0), x ) - 250 )
            H.add_edge(v, 0, time=-math.dist( y, (0,0) ), weight=-math.dist( y, (0,0) ) - 250 )
        
    return H

##################### display_graph() #####################
#####################                 #####################

def display_graph(G, pos=None, node_size=None, with_labels=True, node_attributes=None, edge_attributes=None):
    
    if pos is None:
        pos = nx.spring_layout(G)  # Default position if none provided
    if node_size is None:
        node_size = 100  # Default node size if none provided

    # Handle node attributes (single or multiple)
    if node_attributes is not None:
        labels = {}
        for node, attr in G.nodes(data=True):
            label = f"{node}\n"
            for node_attr in node_attributes:
                value = attr.get(node_attr, 'N/A')
                if isinstance(value, (int, float)):
                    value = round(value, 2)
                label += f"{node_attr[0]}: {value}\n"
            labels[node] = label.strip()  # Remove trailing newline
    else:
        labels = {node: str(node) for node in G.nodes()}  # Default to node identifier
        
    nx.draw(G, pos=pos, labels=labels, node_size=node_size, with_labels=with_labels)
    
    # Handle edge attributes (single or multiple)
    if edge_attributes is not None:
        edge_labels = {}
        for u, v, attr in G.edges(data=True):
            label = ""
            for edge_attr in edge_attributes:
                value = attr.get(edge_attr, 'N/A')
                if isinstance(value, (int, float)):
                    value = round(value, 2)
                label += f"{edge_attr[0]}: {value}\n"
            edge_labels[(u, v)] = label.strip()  # Remove trailing newline
        # Draw the edge labels
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.show()

##################### display_driver_graph() #####################
#####################                        #####################

def display_driver_graph(G, pos=None, node_size=None, with_labels=None, node_attributes=None, edge_attributes=None):

    if pos is None:
        pos = nx.spring_layout(G)
    if node_size is None:
        node_size = 100
    if with_labels is None:
        with_labels = True
    if node_attributes is None:
        node_attributes = ['time']
    if edge_attributes is None:
        edge_attributes = ['time']


    # Handle node attributes (single or multiple)
    if node_attributes is not None:
        labels = {}
        for node, attr in G.nodes(data=True):
            label = f"{node}\n"
            for node_attr in node_attributes:
                value = attr.get(node_attr, 'N/A')
                if isinstance(value, (int, float)):
                    value = round(value, 2)
                label += f"{node_attr[0]}: {value}\n"
            labels[node] = label.strip()  # Remove trailing newline
    else:
        labels = {node: str(node) for node in G.nodes()}  # Default to node identifier
        
    nx.draw(G, labels=labels, pos=pos, node_size=node_size, with_labels=with_labels) 

    # Handle edge attributes (single or multiple)
    if edge_attributes is not None:
        edge_labels = {}
        for u, v, attr in G.edges(data=True):
            label = ""
            for edge_attr in edge_attributes:
                value = attr.get(edge_attr, 'N/A')
                if isinstance(value, (int, float)):
                    value = round(value, 2)
                label += f"{edge_attr[0]}: {value}\n"
            edge_labels[(u, v)] = label.strip()  # Remove trailing newline
        # Draw the edge labels
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.show()

##################### create_driver_cycle() #####################
#####################                       #####################

def create_driver_cycle(G, driver_label):

    if driver_label not in out_neigh(0, G):
        return None, None, None
    
    time = 0
    weight = 0
    sched = []
    C = nx.DiGraph()

    u = 0
    v = driver_label
    sched.append(v)
    time += G.edges[u,v]['time']
    weight += G.edges[u,v]['weight']
    driver = v
    
    C.add_node(v, time=time, driver=driver, pos=G.nodes[v]['pos'], path=sched)
    C.add_edge(0, v, time=time, weight=weight)
    
    next_u = v
    v = child(v, G)
    u = next_u

    count = 0

    while u != 0 and v is not None:

        count += 1
        if count > len(G.nodes):
            #print(f"Infinite driver cycle found for driver_label = {driver_label}")
            time = float('inf')
            u = 0

        else:
            time += G.edges[u,v]['time']
            
            if v != 0:
                sched.append(v)
                
            C.add_node(v, time=time, driver=driver, pos=G.nodes[v]['pos'], path=sched)
            C.add_edge(u, v, time=G.edges[u,v]['time'], weight=G.edges[u,v]['weight'])
                      
            next_u = v
            v = child(v, G)
            u = next_u


    return time, sched, C

#####################  create_driver_array()  #####################
#####################                         #####################

def create_driver_array(G, driver_list=None, wp=True):

    if driver_list is None:
        if 0 in G.nodes:
            if len(list(out_neigh(0, G))) > 0:
                driver_list = list(out_neigh(0, G))
            else:
                print("Zero deliveries from wearhouse node '0' in graph G.")
                driver_list = []
        else:
            print("G must contain wearhouse node '0'.")
            driver_list = []
            
    driver_array = []
    
    for v in driver_list:
    
        driver = Driver(G, v)
        
        if wp:
            print(f"time_C = {driver.time}, sched_C = {driver.sched}")
            display_graph(driver.graph, pos=nx.get_node_attributes(driver.graph, "pos"))

        
        driver_array.append(driver)

    return driver_array

#####################   flip_arc()   #####################
#####################                #####################

def FlipArc(u, v, H):

    #print('fliping arc {} ---> {} in {}'.format(u,v,H.name))
    del_add = []
    ErrorFlag = 0
    if u in H.nodes and v in H.nodes:
        if v in H[u]:
            H.add_edge(v, u, time=-H[u][v]['time'], weight=-H[u][v]['weight'] )
            H.remove_edge(u,v)
        else:
            print('>>>>>>>: Error : FlipArc() <<<<<<< an edge ({},{}) was not found in H.name = {} '.format(u,v,H.name))
            ErrorFlag  = 1
    else:
        print('>>>>>>>: Error : FlipArc() <<<<<<< a node {}, or {} was not found in H.name = {} '.format(u,v,H.name))
        ErrorFlag  = 1

    return ErrorFlag

#####################   aug_path()   #####################
#####################                #####################

def aug_path(P, H_prev):
    
    if H_prev != nx.DiGraph() and len(P) > 2:

        list_augments = []
        delete = []
        add = []
        augment = (delete,add,list_augments)
        
        for i in range(len(P) - 1):
            u = P[i]
            v = P[i+1]
            t = H_prev.edges[u, v]['time']
            w = H_prev.edges[u, v]['weight']
            
            ErrorFlag = FlipArc(u, v, H_prev)
            

            if u == -1:
                a = 0
            else:
                a = u
            if v == -1:
                b = 0
            else:
                b = v

            if u % 2 == 1 and v != 0:   # Central Deletion
                #print(f"Central Deletion {u, v, w}")
                delete.append((b,a))
                list_augments.append((u,v,t,w))
            elif u % 2 == 0 and u != 0:  # Central Addition
                #print(f"Central Addition {u, v, w}")
                add.append((a,b,t,w))
                list_augments.append((u,v,t,w))
            elif u == 0:
                if v % 2 == 0:  # Initial Deletion
                    #print(f"Initial Deletion {u, v, w}")
                    delete.append((b,a))
                    list_augments.append((u,v,t,w))
                else:
                    #print(f"Initial Addition {u, v, w}")
                    add.append((a,b,t,w)) # Initial Addition
                    list_augments.append((u,v,t,w))
            elif v == 0:
                if u % 2 == 0:
                    #print(f"Terminal Addition {u, v, w}")
                    add.append((a,b,t,w)) # Terminal Addition
                    list_augments.append((u,v,t,w))
                else:
                    #print(f"Terminal Deletion {u, v, w}")
                    delete.append((b,a))   # Terminal Deletion
                    list_augments.append((u,v,t,w))
                
            if ErrorFlag == 1:
                augment = ([],[],[])
                print('Arc nonexistent in AugPath()')
                os.system('pause')
        #if augment != ():
            #augment = (delete,add,list_augments)
        
    else:
        print('H_prev.name {} is empty... and/or cannot discharge trivial path P = {} '.format(H_prev.name, P))
        augment = ([],[],[])
        #os.system('pause')
    #print('augment = {}'.format(augment))
    return augment
    
#####################  feasible_check()  #####################
#####################                    #####################

def feasible_check(a, b, path, drivers_x, strength=None, wp=True):

    if strength is None:
        strength = 'strong'

    if strength == 'strong':
        drivers_y, deleted_arcs = strong_feasible_check(a, b, path, drivers_x,  wp=wp) # Here we must use the updated state of the Drivers object at u.
        
    elif strength == 'relaxed':
        drivers_y, deleted_arcs = relaxed_feasible_check(a, b, path, drivers_x, wp=wp) # Here we must use the original state of the Drivers object.

    else:
        print(f"\n############### ::: ERROR type strength = {strength} not recognized. ::: ###############\n ")
        drivers_y = None

    return drivers_y, deleted_arcs

#####################  strong_feasible_check()  #####################
#####################                           #####################

def strong_feasible_check(u, v, path, drivers_u, wp=True):

    #min_path = paths[u][1:] + [u, v]   # NEEDS TO BE FIXED IN DRIVERS OBJECT_3.
   
    X = copy.deepcopy(drivers_u.G)
    time_limit = drivers_u.time_limit
    deleted_arcs = []
    lost_drivers = {}
    

    pos = drivers_u.G.nodes(data='pos')

    if wp:
        print(f"\n________________________________--------------:ENTER strong_feasible_check():----------------_________________________\n")
        print(f"checking current path = {path}")
        print("Driver at vertex u:")
        display_graph(drivers_u.G, pos=pos)
            
    if drivers_u.hot_drivers != {}:
        if wp:
            print(f"A PREVIOUS HOT DRIVER HAS BEEN FOUND!!! hot_drivers = {drivers_u.hot_drivers}, on aug_path = {path}, at (u,v) = {u,v}")

    if u == -1 or u == 0:

        if u == -1 or (u == 0 and v % 2 == 0):
            if wp:
                print(f"Initial Deletion. (u, v) = {u, v}")
            driver_v = drivers_u.G.nodes[v]['driver']

            if (v, 0) in X.edges:
                X.remove_edge(v, 0)                   # Initial Deletion IS a backwards arc in G
            else:
                lost_drivers[ X.nodes[v]['driver'] ] = float('inf')
            
        elif u == 0 and v % 2 == 1:
            if wp:
                print(f"Initial Addition. (u, v, w) = {u, v, math.dist(pos[0], pos[v])} Driver Trade!")
            driver_v = drivers_u.G.nodes[v]['driver']
            
            if (0, v) in X.edges:
                lost_drivers[ X.nodes[v]['driver'] ] = float('inf')
            else:
                X.add_edge(0, v, time=math.dist(pos[0], pos[v]), weight=math.dist(pos[u], pos[v])+250  )

    elif v == -1 or v == 0:

        if v == -1 or (v == 0 and u % 2 == 0):
            if wp:
                print(f"Terminal Addition. (u, v, w) = {u, v, math.dist(pos[u], pos[0])}")
            
            if (u, 0) in X.edges:
                lost_drivers[ X.nodes[u]['driver'] ] = float('inf')
            else:
                X.add_edge(u, 0, time=math.dist(pos[u], pos[0]), weight=math.dist(pos[u], pos[0])+250  )
            

        elif v == 0 and u % 2 == 1:
            if wp:
                print(f"Terminal Deletion. (u, v) = {u, v}")
                
            if (0, u) in X.edges:
                X.remove_edge(0, u)                  # Terminal Deletion IS a backwards arc in G
            else:
                lost_drivers[ X.nodes[u]['driver'] ] = float('inf')
    
    elif v%2 == 1:

        if wp:
            print(f"Central Addition. (u, v, w) = {u, v, math.dist(pos[u], pos[v])}")
        driver_u = drivers_u.G.nodes[u]['driver']
        driver_v = drivers_u.G.nodes[v]['driver']
        if driver_u == driver_v:
            lost_drivers[driver_u] = path
            if wp:
                print(f"Disconnect: Same driver, lost_cycle created!!! (u, v) = {u, v}, driver_v = {driver_v}, driver_u = {driver_u}")
                print(f"LOST driver! = {driver_u} path = {path}")
                

        if (u, v) in X.edges:
            lost_drivers[ X.nodes[v]['driver'] ] = float('inf')
        else:
            X.add_edge(u, v, time=math.dist(pos[u], pos[v]), weight=math.dist(pos[u], pos[v]) )

    elif v%2 == 0:
        
        if wp:
            print(f"Central Deletion. (u, v) = {u, v}")
        driver_u = drivers_u.G.nodes[u]['driver']
        driver_v = drivers_u.G.nodes[v]['driver']
        if driver_u != driver_v:
            if wp:
                print(f"\n:::::::::::::::::<<<<<<<<<<<<<<<( ERROR: CENTRAL DELETION driver_u = {driver_u}, driver_v = {driver_v} NOT EQUAL. )>>>>>>>>>>>>>>>>>::::::::::::::::::\n")
                print(f"                                             LOST DRIVER? = {drivers_u.hot_drivers}, path = {path}\n")
        else:
            if wp:
                print(f"\n:::::::::::::::::<<<<<<<<<<<<<<<( CENTRAL DELETION, CLEAN CUT:            {driver_u} = {driver_v}  EQUAL. )>>>>>>>>>>>>>>>>>::::::::::::::::::\n")
                print(f"                                                      LOST DRIVER? = {drivers_u.hot_drivers}, path = {path}\n")
        
        if (v, u) in X.edges:
            X.remove_edge(v, u)                   # Central Deletion IS a backwards arc in G.
        else:
            lost_drivers[ X.nodes[u]['driver'] ] = float('inf')
        
    drivers_v = Drivers( G=X, H=nx.DiGraph(), time_limit=time_limit, wp=wp )

    if lost_drivers != {}:
        for driver_label in lost_drivers.keys():
            drivers_v.time[driver_label] = float('inf')
            if wp:
                print(f"lost_driver = {driver_label}, lost_drivers[{driver_label}] = {lost_drivers[driver_label]}, drivers_v.hot_drivers = {drivers_v.hot_drivers}")
    
    for driver_label, driver_time in drivers_v.time.items():
        if driver_time > time_limit:
            drivers_v.hot_drivers[driver_label] = driver_time
            if wp:
                print(f"hot_driver = {driver_label}, driver_time = {driver_time}, drivers_v.hot_drivers = {drivers_v.hot_drivers}")
            
            if len(path) == 3:
                if wp:
                    print(f"This arc (u,v)={u,v} will always be hot. It will added to deleted_arcs.")
                deleted_arcs.append((u,v))
    
    if wp:
        print("Driver at vertex v:")
        display_graph(drivers_v.G, pos=pos)
        print(f"updated drivers_v.hot_drivers = {drivers_v.hot_drivers}")
        print(f"\n----------------------------________________:EXIT strong_feasible_check():________________--------------------------------\n")
       
    return drivers_v, deleted_arcs

#####################  relaxed_feasible_check()  #####################
#####################                            #####################

def relaxed_feasible_check(a, b, path, drivers, wp=True):
    
    #min_path = paths[a][1:] + [a, b]  # NEEDS TO BE FIXED IN DRIVERS OBJECT_3.
    deleted_arcs = []
    X = copy.deepcopy(drivers.G)
    hot_drivers = {}
    lost_drivers = {}
    free_driver = None
    visited_drivers = []
    
    pos = drivers.G.nodes(data='pos')
    time_limit = drivers.time_limit

    if wp:
        print(f"\n________________________________--------------:ENTER relaxed_feasible_check():----------------_________________________\n")
        print(f"checking current path = {path}")

    S = {}
    Y = nx.DiGraph()
    Y.add_node( 0, pos=(0, 0), time=None, driver=None )
    
    for node in path:

        if node == -1:
            node = 0

        driver_label = X.nodes[node]['driver']

        if wp:
            print(f"This node = {node} has driver {X.nodes[node]["driver"]}")        
            if driver_label in S:
                print(f"This driver {driver_label} has already been visited in this aug-path {path}")
            else:
                print(f"This driver {driver_label} is visited in this aug-path {path}")
            
        visited_drivers.append(driver_label)

        if driver_label is not None:
            effected_driver_graph = drivers.graphs[driver_label]
            S[driver_label] = effected_driver_graph.copy()
            Y = nx.compose(Y, effected_driver_graph)
            Y.nodes[0]['time'] = None
            Y.nodes[0]['driver'] = None
    
    nbunch = [node for node in Y.nodes if node != 0]
    X.remove_nodes_from(nbunch)

    que_nodes = deque(path)
    que_drivers = deque(visited_drivers)

    if wp:
        print(f"\nque_nodes = {que_nodes} que_drivers = {que_drivers}")
    
    u = None
    v = que_nodes.popleft()

    driver_u = None
    if v == -1:
        driver_v = None
        que_drivers.popleft()
    else:
        driver_v = que_drivers.popleft() 
    
    while que_nodes and que_drivers:

        next_v = que_nodes.popleft()
        u = v
        v = next_v

        driver_u = driver_v
        driver_v = que_drivers.popleft()
        
        if wp:
            print(f"\nState (current) of effect drivers graph: que_nodes = {que_nodes} que_drivers = {que_drivers}\n driver_u = {driver_u}, driver_v = {driver_v}")
            display_driver_graph(Y, pos=pos)
        
        if hot_drivers != {}:
            if wp:
                print(f"A PREVIOUS HOT DRIVER HAS BEEN FOUND!!! hot_drivers = {hot_drivers}, on aug_path = {path}, at (u,v) = {u,v}")

        if lost_drivers != {}:
            if wp:
                print(f"A PREVIOUS LOST DRIVER HAS BEEN FOUND!!! lost_drivers = {lost_drivers}, on aug_path = {path}, at (u,v) = {u,v}")

        if u == -1 or u == 0:

            if u == -1:
                if wp:
                    print(f"Initial Deletion. (u, v) = {u, v}")
                    
                C_v = S[driver_v]
                C_v.remove_edge(v, 0) 
                Y.remove_edge(v, 0) # Deletion is a backwards arc in G
                
                free_driver = driver_v
                
            elif u == 0:
                if wp:
                    print(f"Initial Addition. (u, v) = {u, v} Driver Trade!")
                    
                C_v = S[driver_v]
                C_v.add_edge(0, v, time=math.dist(pos[0], pos[v]) )
                Y.add_edge(0, v, time=math.dist(pos[0], pos[v]) )
                
                free_driver = driver_v

        elif v == -1 or v == 0:

            if v == -1:
                if wp:
                    print(f"Terminal Addition. (u, v) = {u, v}")
                C_u = S[driver_u]
                C_u.add_edge(u, 0, time=math.dist(pos[u], pos[0]) )
                Y.add_edge(u, 0, time=math.dist(pos[u], pos[0]) )
                free_driver = None

            elif v == 0:
                if wp:
                    print(f"Terminal Deletion. (u, v) = {u, v}")
                C_u = S[driver_u]
                C_u.remove_edge(0, u)
                Y.remove_edge(0, u)                  # Deletion is a backwards arc in G
                free_driver = None
        
        elif v%2 == 1:

            if wp:
                print(f"Central Addition. (u, v) = {u, v}")
            
            if driver_u == driver_v:
                if wp:
                    print(f"Disconnect: Same driver, lost_cycle created!!! (u, v) = {u, v}, driver_v = {driver_v}, driver_u = {driver_u}")
                lost_drivers[driver_v] = S[driver_v]

            C_v = S[driver_v]
            C_v.add_edge(u, v, time=math.dist(pos[u], pos[v]) )
            Y.add_edge(u, v, time=math.dist(pos[u], pos[v]) )

            free_driver = driver_v

        elif v%2 == 0:
            
            if wp:
                print(f"Central Deletion. (u, v) = {u, v}")
          
            if driver_u != driver_v:
                print(f"\n:::::::::::::::::<<<<<<<<<<<<<<<( ERROR: CENTRAL DELETION driver_u = {driver_u}, driver_v = {driver_v} NOT EQUAL. )>>>>>>>>>>>>>>>>>::::::::::::::::::\n")
            C_v = S[driver_v]
            C_v.remove_edge(v, u)
            Y.remove_edge(v, u)                   # Deletion is a backwards arc in G
            free_driver = driver_v

    if lost_drivers != {}:
        if wp:
            print(f"lost_drivers = {lost_drivers}")
        for driver_label in lost_drivers.keys():
            hot_drivers[driver_label] = float('inf')

    X = nx.compose(X, Y)
    
    drivers_X = Drivers(X, H=nx.DiGraph(), time_limit=time_limit, wp=wp) # state of drivers object at vertex x (hot drivers is one step ahead case: child(v, H) = sink)

    if wp:
        print(f"drivers_X.G.nodes[0]['time'] = {drivers_X.G.nodes[0]['time']}, drivers_X.G.nodes[0]['driver'] = {drivers_X.G.nodes[0]['driver']},\n drivers_X.time = {drivers_X.time}")
        display_graph(Y, node_attributes=['time', 'driver'], edge_attributes=['time'], pos=pos)
    
    for driver_label, driver_time in drivers_X.time.items():
            if driver_time > time_limit:
                hot_drivers[driver_label] = driver_time
                if wp:
                    print(f"hot_driver = {driver_label}, driver_time = {driver_time}, drivers_X.hot_drivers = {drivers_X.hot_drivers}")
                
                
    if len(path) == 3 and hot_drivers != {}:
        if wp:
            print(f"This arc (u,v)={path[1], path[2]} will always be hot. It will be deleted from drivers.H. path = {path}")
        deleted_arcs.append( (path[1], path[2]) )
    
    if wp:
        print(f"Updated: drivers_X.hot_drivers = {drivers_X.hot_drivers}")

    if free_driver is None:
        if wp:
            print(f"AUGMENT DISCHARGED free_driver = {free_driver}: ")
            print(f"drivers_X.time = {drivers_X.time}")    
            print(f"drivers_X.hot_drivers = {drivers_X.hot_drivers}") 
    else:
        if wp:
            print(f"LIVE WIRE free_driver = {free_driver} is not none. Exiting relaxed_feasible_check()")
            print(f"drivers_X.time = {drivers_X.time}")    
            print(f"drivers_X.hot_drivers = {drivers_X.hot_drivers}") 
    
    if wp:
        print(f"\n----------------------------________________:EXIT relaxed_feasible_check():________________--------------------------------\n")
    return drivers_X, deleted_arcs


#####################   bellman_ford_feasible()  #####################
#####################                            #####################

def bellman_ford_feasible(drivers, source, sink, strength=None, relax_limit=None, time_limit=None, wp=True):

    if wp:
        print(f"\n________________________________--------------:ENTER bellman_ford_feasible():----------------_________________________\n")
    H = drivers.H
    pos = nx.get_node_attributes(drivers.G, 'pos')
    
    if relax_limit is None:
        relax_limit = len(H.nodes()) - 1
    if time_limit is None:
        time_limit = float('inf')
    if strength is None:
        strength = 'strong'

    # Initialize:
    dist = {v: float('inf') for v in H.nodes()}
    dist[source] = 0
    paths = {v: [None] for v in H.nodes()}
    state = {v: Drivers(wp=wp) for v in H.nodes()}
    state[source] = drivers

    deleted_arcs = []
    first_pass = True
    state_change = True

    # Relax edges up to V-1 times
    relax_count = 0
    while state_change and relax_count <= relax_limit:
        relax_count += 1
        if wp:
            print(f"relax_count = {relax_count}, relax_limit = {relax_limit}, len(H.nodes) = {len(H.nodes)}")
        
        state_change = False
        
        for u, v, data in H.edges(data=True):
            
            time_residual = data['time']
            if wp:
                print(f"________________________________------------weight of {u,v} is {time_residual}------------------_________________________")
            if dist[u] + time_residual < dist[v]:

                if strength == 'relaxed':
                    drivers_X, new_deleted_arcs = feasible_check(u, v, paths[u][1:]+[u,v], drivers, strength=strength, wp=wp)
                elif strength == 'strong':
                    drivers_X, new_deleted_arcs = feasible_check(u, v, paths[u][1:]+[u,v], state[u], strength=strength, wp=wp)
                if new_deleted_arcs != []:
                    deleted_arcs = deleted_arcs + new_deleted_arcs
                    
                if wp:
                    print(f"feasible arc found (u,v) = {u,v}, on path {paths[u]}")
                    print(f"Resulting State of Drivers u, and v:")
                    for driver_label in drivers_X.labels:
                        print(f"driver = {driver_label}, sched = {drivers_X.sched[driver_label]}, time = {drivers_X.time[driver_label]}")
                        #display_graph(drivers_X.graphs[driver_label], node_attributes=['time', 'driver'], edge_attributes=['time'], pos=pos)
                    print(f"----------------------------------------------------------------------------------------------------------------\n")
                
                if drivers_X.hot_drivers == {}:
                    if wp:
                        print(f"Pred Modified! pred of v({v}) = {paths[v][-1]},\n paths = {paths[v]}")

                    dist[v] = dist[u] + time_residual
                    paths[v] = paths[u] + [u]
                    state[v] = drivers_X

                    state_change = True
                    
                    if len(paths[v]) > len(H.nodes)  - 1:
                        print(f"\nNegative Cycle Detected (path length > n-1).\n paths[v] = {paths[v]}")

                    S = set(paths[v])
                    if len(S) != len(paths[v]):
                        print(f"\nNegative Cycle Detected (set size differs).\n paths[v] = {paths[v]}")

                else:
                    if wp:
                        print(f"Edge {u, v} ignored (hot_drivers = {drivers_X.hot_drivers}):")
    
            else:
                if wp:
                    print(f"Edge {u, v} ignored (not shorter):")
                    print(f"dist[{u}] = {dist[u]}, time_residual = {time_residual}, dist[{v}] = {dist[v]}.")
        if wp:          
            print("<<::: Edge Pass Complete :::>>>\n")
        if first_pass:
            print(f"deleting arcs from: len(deleted_arcs) = {len(deleted_arcs)} ")
            drivers.H.remove_edges_from(deleted_arcs)
            first_pass = False
        

    if relax_count == len(H.nodes) - 1:
        # Check for negative weight cycles and identify the cycle
        if wp:
            print("Check for negative weight cycles and identify the cycle")
        for u, v, data in H.edges(data=True):
            time_residual = data['time']
            
            # Check the time constraint during cycle detection as well
            if dist[u] + time_residual < dist[v]:
                if wp:
                    print(f"Negative weight cycle detected at edge (u={u}, v={v}) with dist[{u}] = {dist[u]}, time = {time}, dist[{v}] = {dist[v]}")
                if strength == 'relaxed':
                    drivers_X, deleted_arcs = feasible_check(u, v, paths[u][1:]+[u,v], drivers, strength=strength, wp=wp)
                elif strength == 'strong':
                    drivers_X, deleted_arcs = feasible_check(u, v, paths[u][1:]+[u,v], state[u], strength=strength, wp=wp)
                if new_deleted_arcs != []:
                    print("THIS PROBABLY SHOULD NOT HAVE HAPPEND HERE.")
                    deleted_arcs = deleted_arcs + new_deleted_arcs
                    
                if wp:
                    print(f"hot_driver = {hot_drivers}, pred of v({v}) = {paths[v][-1]},\n paths = {paths[v]}")
                if drivers_X.hot_drivers == {}:
                    
                    # To find the cycle, we need to trace back from 'v' until we see a repeat node
                    cycle = []
                    visited = set()
                    current_v = v
        
                    while current_v not in visited:
                        if wp:
                            print(f"current_v = {current_v}, pred of ({current_v}) = {paths[current_v][-1]}")     
                        visited.add(current_v)
                        current_v = paths[current_v][-1] # pred[v] = paths[v][0] predecessor of v is the first thing in the path
        
                    # Now current_node is part of the cycle, trace the cycle
                    cycle_start = current_v
                    cycle = [cycle_start]
                    current_v = paths[cycle_start][-1]
        
                    while current_v != cycle_start:
                        cycle.append(current_v)
                        current_v = paths[current_v][-1]
        
                    cycle.append(cycle_start)  # Complete the cycle
        
                    cycle.reverse()  # To return the cycle in the correct order
                    if wp:
                        print(f"Negative-Cycle Found: hot_drivers = {hot_drivers}")
                    
                    return paths, cycle

    if wp:
        print(f"\n----------------------------________________:EXIT bellman_ford_feasible():________________--------------------------------\n")
    return paths, None



#####################   discharge_bellman_ford()  #####################
#####################                             #####################

def discharge_bellmanford(drivers, time_limit=None, relax_limit=None, strength=None, wp=True):
    
    paths, cycle = bellman_ford_feasible(drivers, -1, 0, relax_limit=relax_limit, time_limit=time_limit, strength=strength, wp=wp)

    if cycle is not None:
        
        return None, cycle
    
    if paths[0] != [None]:
        min_path = paths[0][1:] + [0]
    else:
        min_path = None

    #if wp:
    print(f"\nDischarging: min_path = {min_path}, cycle = {cycle}.")
            
    if min_path is None:
        #paths_forward, cycle_forward = bellman_ford_feasible(drivers_1, 0, -1, relax_limit=relax_limit, time_limit=time_limit, wp=wp)
        #print(f"path_forward = {paths_forward}, cycle_forward = {cycle_forward}.")

        return None, cycle
    
    else:
        P = min_path
        augment = aug_path(P, drivers.H)

        ebunch_del = augment[0]
        ebunch_add = augment[1]
        aug_list = augment[2]
    
        if wp:
            print(f"ebunch_del = {ebunch_del}, ebunch_add = {ebunch_add}, aug_list = {aug_list}")
        
        drivers.G.remove_edges_from(ebunch_del)
        
        for edge in ebunch_add:
            drivers.G.add_edge(edge[0], edge[1], weight=edge[2], time=edge[2])
    
        for aug_item in aug_list:
            u, v = aug_item[0], aug_item[1]
            w = aug_item[3] if len(aug_item) > 3 else aug_item[2]
            if v > 0 and v%2 == 1:
                driver_u = drivers.G.nodes[u]['driver']
                driver_v = drivers.G.nodes[v]['driver']
                sched_u = drivers.G.nodes[u]['path']
                sched_v = drivers.G.nodes[v]['path']
                sched_driver_u = drivers.sched[driver_u]
                sched_driver_v = drivers.sched[driver_v]
    
                if wp:
                    print(f"driver trade driver_u = {driver_u}, driver_v = {driver_v}")
                    print(f"sched_driver_u = {sched_driver_u}, sched_driver_v = {sched_driver_v}")
                    print(f"sched_u = {sched_u}, sched_v = {sched_v}")
                    print(f"sched_driver_u_remaining = {sched_driver_v[len(sched_v):]}")
                    print(f"sched_driver_v_new = {sched_u + sched_driver_v[len(sched_v)-1:]}")
                    print(f"sched_driver_u_new = {sched_v[:-2]}")
    
        if wp:
            display_graph(drivers.H, pos=pos_residual)
            display_graph(drivers.G, pos=pos_euclidean, edge_attributes=['time'])
        
            for driver in drivers.drivers.values():
                print(f"driver = {driver.label}, drivers.time[{driver.label}] = {drivers.time[driver.label]}")
                display_driver_graph(drivers.graphs[driver.label], pos=pos_euclidean, node_attributes=['path'])
    
        effected_vertices = min_path[1:-1]
        effected_drivers = []
        
        for v in effected_vertices:
            effected_drivers.append(drivers.G.nodes[v]['driver'])
    
        if wp:
            print(f"effected_vertices = {effected_vertices}")
            print(f"effected_drivers = {effected_drivers}")
            
        drivers.update()
    
        if wp:
            display_graph(drivers.H, pos=pos_residual)
            display_graph(drivers.G, pos=pos_euclidean, edge_attributes=['time'], node_attributes=['time', 'driver'])
        
            for driver in drivers.drivers.values():
                print(f"driver = {driver.label}, drivers.time[{driver.label}] = {drivers.time[driver.label]}")
                display_driver_graph(drivers.graphs[driver.label], pos=pos_euclidean, edge_attributes=['time'], node_attributes=['time', 'driver'])

    return min_path, cycle

#####################   ()  #####################
#####################                             #####################




#####################   ()  #####################
#####################                             #####################





#####################   ()  #####################
#####################                             #####################