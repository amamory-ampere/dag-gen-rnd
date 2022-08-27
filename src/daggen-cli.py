#!/usr/bin/python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------------
# Randomized Multi-DAG Task Generator
# Xiaotian Dai
# Real-Time Systems Group
# University of York, UK
# -------------------------------------------------------------------------------

import os, sys, logging, getopt, time, json
import networkx as nx
import random
#from tqdm import tqdm

from rnddag import DAG, DAGTaskset
from generator import uunifast_discard, uunifast
from generator import gen_period, gen_execution_times


def parse_configuration(config_path):
    try:
        with open(config_path, "r") as config_file:
            config_json = json.load(config_file)
    except:
        raise EnvironmentError("Unable to open %s" % (config_path))

    return config_json


def print_usage_info():
    logging.info("[Usage] python3 daggen-cli.py --config config_file")

# return the path and the path lenght with the longest C
# which corresponds to the DAG critial path
def longest_dag_path(graph):
    assert(graph.in_degree(0) == 0)
    dist = dict.fromkeys(graph.nodes, -float('inf'))
    dist[0] = 0
    weight = dict.fromkeys(graph.nodes, 0)
    nx.set_node_attributes(graph, weight, 'weight')
    nx.set_node_attributes(graph, weight, 'longest')
    # for n,data in graph.nodes(data=True):
    #     print (n,":", data)
    #     for s,t,edata in graph.edges(n,data=True):
    #         print (" - ", s,t, edata)
    topo_order = nx.topological_sort(graph)
    for n in topo_order:
        for s in graph.successors(n):
            if graph.nodes[s]['C'] + graph.nodes[n]['weight'] > graph.nodes[s]['weight']:
                graph.nodes[s]['weight'] = graph.nodes[s]['C'] + graph.nodes[n]['weight']
                graph.nodes[s]['longest'] = n

    longest_path_lenght = graph.nodes[G.get_number_of_nodes()-1]['weight']
    # start w the last node
    latest_node = G.get_number_of_nodes()-1
    assert(graph.out_degree(latest_node) == 0)
    longest_path = [latest_node]
    while(1):
        previous_node = graph.nodes[longest_path[0]]['longest']
        assert(previous_node>=0)
        longest_path.insert(0,previous_node)
        # until it reaches the initial node
        if graph.in_degree(previous_node) == 0:
            break

    return (longest_path_lenght,longest_path)

if __name__ == "__main__":
    ############################################################################
    # Initialize directories
    ############################################################################
    src_path = os.path.abspath(os.path.dirname(__file__))
    base_path = os.path.abspath(os.path.join(src_path, os.pardir))

    data_path = os.path.join(base_path, "data")
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    logs_path = os.path.join(base_path, "logs")
    if not os.path.exists(logs_path):
        os.makedirs(logs_path)

    ############################################################################
    # Parse cmd arguments
    ############################################################################
    config_path = os.path.join(base_path, "config.json")
    directory = None
    load_jobs = False
    evaluate = False
    train = False

    try:
        short_flags = "hc:d:e"
        long_flags = ["help", "config=", "directory=", "evaluate"]
        opts, args = getopt.getopt(sys.argv[1:], short_flags, long_flags)
    except getopt.GetoptError as err:
        logging.error(err)
        print_usage_info()
        sys.exit(2)

    logging.info("Options:", opts)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_usage_info()
            sys.exit()
        elif opt in ("-c", "--config"):
            config_path = arg
        elif opt in ("-d", "--directory"):
            directory = arg
            load_jobs = True
        elif opt in ("-e", "--evaluate"):
            evaluate = True
        else:
            raise ValueError("Unknown (opt, arg): (%s, %s)" % (opt, arg))

    # load configuration
    config = parse_configuration(config_path)

    logging.info("Configurations:", config)

    ############################################################################
    # load generator basic configuration
    ############################################################################
    # load and set random seed
    random.seed(config["misc"]["rnd_seed"])

    # single- or multi-dag
    multi_dag = config["misc"]["multi-DAG"]

    # DAG config
    dag_config = config["dag_config"]

    ############################################################################
    # I. single DAG generation
    ############################################################################
    if not multi_dag:
        n = config["single_task"]["set_number"]
        w = config["single_task"]["workload"]
        assert(dag_config["period"]>=dag_config["deadline"])

        # for i in tqdm(range(n)):
        i=0
        while i < n:
            # create a new DAG
            G = DAG(i=i, U=-1, T=-1, W=w, 
                period = dag_config["period"],
                deadline = dag_config["deadline"])
            G.gen_rnd(parallelism=dag_config["parallelism"],
                      layer_num_min=dag_config["layer_num_min"],
                      layer_num_max=dag_config["layer_num_max"],
                      connect_prob=dag_config["connect_prob"])

            # skip invalid dags
            if G.get_graph()== None:
                continue
                
            # generate sub-DAG execution times
            n_nodes = G.get_number_of_nodes()
            dummy = config["misc"]["dummy_source_and_sink"]
            c_ = gen_execution_times(n_nodes, w, round_c=True, dummy=dummy)
            # C_ns is set to be up to 10% of C
            c_ns_ = {key: random.randint(0, int(value * 0.1)) for key, value in c_.items()}
            # print (type(c_))
            # for key,value in c_.items():
            #     print(key, ':', value)
            # new_c = {}
            # new_c_ns = {}
            # for k, v in c_.items():
            #     new_c[k] = max(int(v * 0.9), 0)
            #     new_c_ns[k] = random.randint(0, int(v * 0.1))
            # # for key,value in new_c.items():
            # #     print(key, ':', value)
            # # for key,value in new_c_ns.items():
            # #     print(key, ':', value)
            
            nx.set_node_attributes(G.get_graph(), c_, 'C')
            nx.set_node_attributes(G.get_graph(), c_ns_, 'C_ns')

            # set execution times on edges
            w_e = {}
            # for e in G.get_graph().edges():
            #     ccc = new_c[e[0]] + new_c_ns[e[0]]
            #     w_e[e] = ccc
            # the edges now represent the max number of bytes sent between sender/receiver
            for e in G.get_graph().edges():
                w_e[e] = random.randint(1,dag_config["max_bytes"])

            nx.set_edge_attributes(G.get_graph(), w_e, 'label')

            # calculate the longest path assuming C
            [critical_length, critical_path] = longest_dag_path(G.get_graph())
            # print ('path:', critical_path, 'has lenght:',critical_length)
            # ignore the graph if it violated the end-to-end dag deadline
            if critical_length > dag_config["deadline"]:
                continue
            
            # set the edge colors to indicate the dag critical path
            c_e = {}
            for e in G.get_graph().edges():
                if e[0] in critical_path and e[1] in critical_path:
                    c_e[e] = 'red'
                else:
                    c_e[e] = 'black'
            nx.set_edge_attributes(G.get_graph(), c_e, 'color')

            # save the dag critical path lenght into the dag for debug purporses
            G.get_graph().graph['critical_path_length'] = critical_length

            # print internal data
            if config["misc"]["print_DAG"]:
                G.print_data()

            # save graph
            if config["misc"]["save_to_file"]:
                G.save(basefolder="./data/")
            i+=1

    ############################################################################
    # II. multi-DAG generation
    ############################################################################
    else:
        # set of tasksets
        n_set = config["multi_task"]["set_number"]

        # total utilization
        u_total = config["multi_task"]["utilization"]

        # task number
        n = config["multi_task"]["task_number_per_set"]

        # number of cores
        cores = config["misc"]["cores"]

        # Load DAG period set (in us)
        period_set = config["multi_task"]["periods"]
        period_set = [(x) for x in period_set]

        # DAG generation main loop
        for set_index in tqdm(range(n_set)):
            logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            # create a new taskset
            Gamma = DAGTaskset()

            U_p = []

            # DAG taskset utilization
            U = uunifast_discard(n, u=u_total, nsets=n_set, ulimit=cores)

            # generate periods
            periods = gen_period(period_set, n)
            logging.info(periods)

            for i in range(n):
                # calculate workload (in us)
                w = U[set_index][i] * periods[i]

                # create a new DAG
                G = DAG(i=i, U=U[set_index][i], T=periods[i], W=w)

                # generate nodes in the DAG
                # G.gen_nfj()
                G.gen_rnd(parallelism=dag_config["parallelism"],
                          layer_num_min=dag_config["layer_num_min"],
                          layer_num_max=dag_config["layer_num_max"],
                          connect_prob=dag_config["connect_prob"])

                # generate sub-DAG execution times
                n_nodes = G.get_number_of_nodes()
                dummy = config["misc"]["dummy_source_and_sink"]
                c_ = gen_execution_times(n_nodes, w, round_c=True, dummy=dummy)
                nx.set_node_attributes(G.get_graph(), c_, 'C')

                # calculate actual workload and utilization
                w_p = 0
                for item in c_.items():
                    w_p = w_p + item[1]

                u_p = w_p / periods[i]
                U_p.append(u_p)

                # print("Task {}: U = {}, T = {}, W = {}>>".format(i, U[0][i], periods[i], w))
                # print("w = {}, w' = {}, diff = {}".format(w, w_p, (w_p - w) / w * 100))

                # set execution times on edges
                w_e = {}
                for e in G.get_graph().edges():
                    ccc = c_[e[0]]
                    w_e[e] = ccc

                nx.set_edge_attributes(G.get_graph(), w_e, 'label')

                # print internal data
                if config["misc"]["print_DAG"]:
                    G.print_data()
                    logging.info("")

                # save the graph
                if config["misc"]["save_to_file"]:
                    G.save(basefolder="./data/data-multi-m{}-u{:.1f}/{}/".format(cores, u_total, set_index))

                # (optional) plot the graph
                # G.plot()

            logging.info("Total U:", sum(U_p), U_p)
            logging.info("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            logging.info("")
