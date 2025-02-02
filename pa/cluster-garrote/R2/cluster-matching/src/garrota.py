import sys
import math
import copy
from sets import Set
from graph_interactions import *
from pimrc_extractor import *


# =========================================================================
# === DISCLAIMER: following functions extract values using PIMRC18 JSON ===
# =========================================================================
def host_fullness(scenario, host_name):
    """Gets the percentage of usage of each host resource

    :scenario: PIMRC18 scenario JSON
    :host_name: unique host name in the scenario
    :returns: dictionary indexed by resources and its percentage usage

    """
    cap = host_capabilities(scenario, host)
    remain_cap = remain_host_capabilities(scenario, host)
    fullness = {}
    for capability in cap:
        fullness[capability] = remain_cap[capability] / cap[capability]

    return fullness


def host_availability(scenario, host_name):
    """Gets the percentage of available resources

    :scenario: PIMRC18 scenario JSON
    :host_name: unique host name in the scenario
    :returns: dictionary indexed by resources and its percentage availability

    """
    availability = host_fullness(scenario, host_name)
    for capability in availability:
        availability[capability] = float(1 - availability[capability])

    return availability


def host_availability_mean(scenario, host_name):
    """Gets the mean of availability percentage for resources

    :scenario: PIMRC18 scenario JSON
    :host_name: unique host name in the scenario
    :returns: availability mean of resources expressed in percentage

    """
    # Get the mean resource availability percentage
    availability = host_availability(scenario, host)
    availability_mean = float(0)
    for capability in availability:
        availability_mean += availability[capability]
    availability_mean /= len(availability.keys())

    return availability_mean
    

def host_unbalance(scenario, host_name):
    """Determines the host unbalancing attending to its resources availability.

    :scenario: PIMRC18 scenario JSON
    :host_name: unique host name in the scenario
    :returns: float number representing host unbalance

    """
    # Unbalancing calculation
    availability_mean = host_availability_mean(scenario, host_name)
    unbalance = 0
    for resource in availability:
        unbalance += math.abs(availability[resource] - availability_mean)

    return unbalance
    

def map_unbalance(capabilities, available_capabilities, req_capabilities):
    """Determines the host unbalancing after a VNF is mapped.

	:capabilities: dictionary of resource-value pairs
	:available_capabilities: dictionary of resource-value pairs
    :req_capabilities: dictionary of resource-value pairs of requested
                       resources
    :returns: float number representing host unbalance

    """
    # Calculate how much of each resource consumes the VNF in the host
    # (expressed in percentage)
    vnf_consum = {}
    for cap in req_capabilities:
        vnf_consum[cap] = req_capabilities[cap] / capabilities[cap]

    # Get resource availability mean after mapping
    available_capabilities_mean = float(0)
    for cap in req_capabilities:
        available_capabilities_mean += available_capabilities[cap] -\
                vnf_consum[cap]
    available_capabilities_mean /= len(req_capabilities.keys())

    # Unbalancing calculation
    unbalance = 0
    for resource in req_capabilities:
        unbalance += math.abs(available_capabilities[resource] -\
                vnf_consum[resource] - available_capabilities_mean)

    return unbalance


# ============================================
# ==== FUNCTIONS AGNOSTIC OF PIMRC18 OR NETWORKX REPRESENTATION ====
# ============================================

# Internally, mapping info is held like this:
# host_node = {
#   "cluster": 1,  
#   "host_name": "h1", 
#   "capabilities": {
#     "storage": 1000, 
#     "cpu": 16, 
#     "memory": 128 
#   },
#   "free_capabilities": {
#     "storage": 900, 
#     "cpu": 14, 
#     "memory": 103
#   },
#   "mapped_vnfs": ["vnf1", "vnf2"],
#   "costs": {
#     "vnf1": 3,
#     "vnf2": 4
#   }
# }
#
# host_edge = 
# {
#   "delay": 0.001,
#   "source": "h1",
#   "capacity": 1000,
#   "free_capacity": 850,
#   "target": "h2",
#   "mapped_vnf_edges": [
#     {
#       "source": "vnf_1",
#       "target": "vnf_2"
#     },
#    ...
#   ]
# }
#
# vnf_node = {
#   "vnf_name": "vnf1", 
#   "processing_time": 4, 
#   "place_at": [
#     "h1"
#   ],
#   "requirements": {
#     "storage": 10, 
#     "cpu": 1, 
#     "memory": 4
#   }, 
#   "cluster": 1,
#   "host_cluster": 4
# }
#
# vnf_edge = {
#   "source": "vnf1",
#   "traffic": 10,
#   "target": "vnf2",
#   "place_at": [
#     {
#       "source": "h1",
#       "target": "h2"
#     },
#     ...
#   ]
# }
#}


def resources_fullness(capabilities, used_capabilities):
    """Gets the percentage of usage of each capability

	:capabilities: dictionary of resource-value pairs
	:used_capabilities: dictionary of resource-value pairs
    :returns: dictionary of resource-percentage pairs

    """
    fullness = {}
    for capability in [cap for cap in capabilities\
                            if type(cap) in [float,int]]:
        fullness[capability] =\
			 float(used_capabilities[capability]) / capabilities[capability]

    return fullness


def resources_availability(capabilities, used_capabilities):
    """Gets the percentage of availability of each capability

	:capabilities: dictionary of resource-value pairs
	:used_capabilities: dictionary of resource-value pairs
    :returns: dictionary of resource-percentage pairs

    """
    availability = resources_fullness(capabilities, used_capabilities)
    print('availability capas: ' + str(availability.keys()))
    print('\t capas:' + str(capabilities))
    print('\t ised:' + str(used_capabilities))
    for capability in availability:
        availability[capability] = 1 - availability[capability]

    return availability


def resources_availability_mean(capabilities, used_capabilities):
    """Gets the mean of availability percentage for resources

	:capabilities: dictionary of resource-value pairs
	:used_capabilities: dictionary of resource-value pairs
    :returns: mean accross the resources availability

    """
    # Get the mean resource availability percentage
    availability = resources_availability(capabilities, used_capabilities)
    availability_mean = float(0)
    for capability in availability:
        availability_mean += availability[capability]
    availability_mean /= len(availability.keys())

    return availability_mean
    

def resources_unbalance(capabilities, used_capabilities):
    """Determines the capabilities unbalancing attending to its
    resources availability.

	:capabilities: dictionary of resource-value pairs
	:used_capabilities: dictionary of resource-value pairs
    :returns: unbalancing according to the capabilities and used dict

    """
    # Unbalancing calculation
    availability = resources_availability(capabilities, used_capabilities)
    availability_mean = resources_availability_mean(capabilities,
        used_capabilities)
    unbalance = 0
    for resource in availability:
        unbalance += abs(availability[resource] - availability_mean)

    return unbalance
    

def map_unbalance(capabilities, used_capabilities, req_capabilities):
    """Determines the host unbalancing after a VNF is mapped.

	:capabilities: dictionary of resource-value pairs
	:used_capabilities: dictionary of resource-value pairs
    :req_capabilities: dictionary of resource-value pairs of requested
                       resources
    :returns: unbalance according to capabilities and used ones after the
              requested ones are mapped

    """
    # Calculate how much of each resource consumes the VNF in the host
    # (expressed in percentage)
    req_consum = {}
    req_caps = [cap for cap in req_capabilities\
                    if type(req_capabilities[cap]) in [float, int]\
                    and req_capabilities[cap] > 0]

    # If no resources required, unbalance is zero
    if len(req_caps) == 0:
        return 0

    for cap in req_caps:
        req_consum[cap] = float(req_capabilities[cap]) / capabilities[cap]

    # Get resource availability mean after mapping
    print('these are the capabilities: ' + str(capabilities))
    print('these are the used capabilities: ' + str(used_capabilities))
    availability = resources_availability(capabilities, used_capabilities)
    availability_mean = float(0)
    print('availability: ' + str(availability))
    print('req_caps: ' + str(req_caps))
    for cap in req_caps:
        availability_mean += availability[cap] - req_consum[cap]
    availability_mean /= float(len(req_caps))

    # Unbalancing calculation
    unbalance = 0
    for resource in req_caps:
        unbalance += abs(availability[resource] - req_consum[resource]\
            - availability_mean)

    return unbalance


def map_unbalance2(capabilities, available_capabilities, req_capabilities):
    """Determines the host unbalancing after a VNF is mapped.
    Like map_unbalance() but providing available_capabilities

	:capabilities: dictionary of resource-value pairs
	:available_capabilities: dictionary of resource-value pairs
    :req_capabilities: dictionary of resource-value pairs of requested
                       resources
    :returns: unbalance according to capabilities and used ones after the
              requested ones are mapped

    """
    # Calculate how much of each resource consumes the VNF in the host
    # (expressed in percentage)
    req_consum = {}
    for cap in [c for c in req_capabilities\
                    if type(req_capabilities[c]) == int\
                    or type(req_capabilities[c]) == float]:
        req_consum[cap] = float(req_capabilities[cap]) / capabilities[cap]

    # Get resource availability mean after mapping
    availability = available_capabilities
    availability_mean = float(0)
    for cap in [c for c in req_capabilities\
                        if type(req_capabilities[c]) == int\
                        or type(req_capabilities[c]) == float]:
        availability_mean += availability[cap] - req_consum[cap]
    availability_mean /= float(len(req_capabilities.keys()))

    # Unbalancing calculation
    unbalance = 0
    for resource in [c for c in req_capabilities\
                        if type(req_capabilities[c]) == int\
                        or type(req_capabilities[c]) == float]:
        unbalance += abs(availability[resource] - req_consum[resource]\
            - availability_mean)

    return unbalance


# ======================================================
# === From here on all is about the cluster matching ===
# ======================================================


def can_map_clusters(ns_cluster, nfvi_pop_cluster):
    """Checks if a NS cluster can be mapped to a hosts cluster

    :ns_cluster: nextorkX cluster with VNFs
    :nfvi_pop_cluster: networkX cluster with NFVI PoPs
    :returns: boolean telling if ns_cluster can be mapped to nfvi_pop_cluster

    """
    if not in_nfvi_cluster(ns_cluster, nfvi_pop_cluster):
        return False
    
    for vnf in ns_cluster.nodes():
        vnf_node = get_vnf(ns_cluster, vnf)
        exists_nfvi_pop, nfvi_pop_id = exist_capable_nfvi_pop(vnf_node,
                nfvi_pop_cluster)
        if not exists_nfvi_pop:
            return False

    for vl in get_vls(ns_cluster):
        if not exist_capable_edge(nfvi_pop_cluster, ns_cluster, vl):
            return False

    
    return enough_cluster_res(ns_cluster, nfvi_pop_cluster)


def garrote_best_nfvi_pop_cluster(ns_cluster, nfvi_pop_clusters):
    """Choose the best NFVI PoP cluster to map a NS cluster

    :ns_cluster: networkX NS cluster instance
    :nfvi_pop_clusters: dictionary with NFVI PoPs clusters
    :returns: {'nfvi_pop_cluster': 1, 'cost': 2, 'unbalance': 3}
              {} if no NFVI PoP cluster can host it

    """
    map_props = {
        'cost': sys.maxint,
        'unbalance': sys.maxint,
        'nfvi_pop_cluster': 'h_fake'
    }

    # Retrieve aggregated info for host clusters
    nfvi_pop_clusters_cap = {}
    for nfvi_pop_cl_name in nfvi_pop_clusters:
        nfvi_pop_cluster = nfvi_pop_clusters[nfvi_pop_cl_name]

        nfvi_pop_clusters_cap[nfvi_pop_cl_name] = {
            'nfvi_pop_cl_capab': nfvi_pop_cluster_cap(nfvi_pop_cluster),
            'nfvi_pop_cl_free_cap': nfvi_pop_cluster_free_cap(nfvi_pop_cluster)
        }

    ns_cl_req = ns_cluster_vnf_req(ns_cluster)


    # Decide best NFVI PoPs cluster to map NS clusters
    for nfvi_pop_cl_name in nfvi_pop_clusters:
        nfvi_pop_cluster = nfvi_pop_clusters[nfvi_pop_cl_name]
        if can_map_clusters(ns_cluster, nfvi_pop_cluster):
            unbalance = map_unbalance2(
                nfvi_pop_clusters_cap[nfvi_pop_cl_name]['nfvi_pop_cl_capab'],
                nfvi_pop_clusters_cap[\
                        nfvi_pop_cl_name]['nfvi_pop_cl_free_cap'],
                ns_cl_req
            )
            cost = cluster_match_cost(ns_cluster,
                       nfvi_pop_clusters[nfvi_pop_cl_name])

            # Best mapping
            if cost < map_props['cost'] or\
                (cost == map_props['cost'] and\
                    unbalance < ns_cl_unbalance['unbalance']):
                map_props['nfvi_pop_cluster'] = nfvi_pop_cl_name
                map_props['cost'] = cost
                map_props['unbalance'] = unbalance
    
    return map_props if map_props['nfvi_pop_cluster'] != 'h_fake' else {}


def garrote_best_cluster_matching(nfvi_pop_clusters, ns_clusters):
    """Obtains the best NS-cluster to NFVI-PoP-cluster matching

    :nfvi_pop_clusters: dictionary of networkX clusters indexed by host cluster
                    name
    :ns_clusters: dictionary of networkX clusters indexed by NS cluster name
    :returns: dictionary with the mapping:
              {
                'ns_cluster': 'fake_ns_cl',
                'nfvi_pop_cluster': 'fake_cl_name',
                'cost': sys.maxint,
                'unbalance': sys.maxint
              }
              if no matching is possible, dict['ns_cluster']=None

    """

    # Find the best mapping
    best_map = {
        'ns_cluster': None,
        'nfvi_pop_cluster': None,
        'cost': sys.maxint,
        'unbalance': sys.maxint
    }
    for ns_cl_name in ns_clusters:
        map_props = garrote_best_nfvi_pop_cluster(
                ns_clusters[ns_cl_name], nfvi_pop_clusters)
        if map_props != {}:
            map_props['ns_cluster'] = ns_cl_name
            if map_props['cost'] < best_map['cost'] or\
                (map_props['cost'] == best_map['cost']) and\
                    (map_props['unbalance'] < best_map['unbalance']):
                best_map = map_props

    return best_map


def garrote_matching(pa_req, legacy_reqs):
    """Performs the cluster matching using garrote heuristic

    :pa_req: API PARequest dictionary
    :legacy_reqs: a list of previous requests with the same underlying NFVI as
    the pa_req parameter
    :note: for the moment legacy_reqs are unused
    :note: each VNF in the PA API req has 'nfviPoPCluster' to specify in which
           NFVI PoP cluster is mapped
    :returns: a API PARequest dict extended with mapping decisions
              and a boolean telling if the matching worked

    """
    nfvi_pop_clusters = create_nfvi_pop_clusters(pa_req)
    ns_clusters = create_ns_clusters([pa_req])
    fake_reducts = []
    

    can_map_more, remain_ns_cl = True, len(ns_clusters.keys()) 
    while can_map_more and remain_ns_cl > 0:
        mapping = garrote_best_cluster_matching(nfvi_pop_clusters, ns_clusters)
        if not mapping['ns_cluster']:
            print '  !!ERR: garrote_best_cluster_matching() cannot find ' +\
                'any cluster match'
            return pa_req, False
        ns_cl = ns_clusters[mapping['ns_cluster']]


        consumption = {
            'host': ns_cluster_vnf_req(ns_cl),
            'link': ns_cluster_edge_req(ns_cl)
        }
        fake_cluster_cap_reduction(
            nfvi_pop_clusters[mapping['nfvi_pop_cluster']],
            consumption
        )
        fake_reducts.append((nfvi_pop_clusters[mapping['nfvi_pop_cluster']],
            consumption))

        # Update PARequest JSON to specify matching
        for vnf in ns_cl.nodes():
            for i in range(len(pa_req['nsd']['VNFs'])):
                if pa_req['nsd']['VNFs'][i]['VNFid'] == vnf:
                    pa_req['nsd']['VNFs'][i]['nfviPoPCluster'] =\
                        mapping['nfvi_pop_cluster']
                    pa_req['nsd']['VNFs'][i]['NFVIPoPid'] =\
                        mapping['nfvi_pop_cluster']

        del ns_clusters[mapping['ns_cluster']]
        remain_ns_cl = len(ns_clusters.keys())

    # Restore the fake reductions
    for (nfvi_pop_cluster, consumption) in fake_reducts:
        for capH in consumption['host']:
            consumption['host'][capH] *= -1
        for capL in consumption['link']:
            consumption['link'][capL] *= -1
        fake_cluster_cap_reduction(nfvi_pop_cluster, consumption)

    return pa_req, True


def garrote_best_vnf_nfvi_pops(pa_req, vnf_node, nfvi_pop_cluster,
        nfvi_pops_graph):
    """Obtains a list with the best hosts to map a VNF. The list is ordered by
    cost and unbalance reduction.

    :pa_req: API PARequest dictionary
    :vnf_node: dictionary with all the VNF properties (obtained with get_vnf())
    :nfvi_pop_cluster: networkX multi-graph instance with a NFVI PoPs cluster
    :nfvi_pops_graph: networkX multi-graph instance the hosts
    :returns: a list of host IDs referenced in nfvi_pop_cluster and nfvi_pops_graph

    """
    best_nfvi_pops = []
    vnf_id = vnf_node['VNFid']

    for nfvi_pop_name in nfvi_pop_cluster.nodes():
        nfvi_pop = get_nfvi_pop(nfvi_pops_graph, nfvi_pop_name)
        if vnf_id in nfvi_pop['costs'] and can_host_vnf(nfvi_pop, vnf_node):
            best_nfvi_pops.append(nfvi_pop)

    # Sort the list of candidate hosts
    def which_is_better(nfvi_pop1, nfvi_pop2):
        if nfvi_pop1['costs'][vnf_id] != nfvi_pop2['costs'][vnf_id]:
            res = nfvi_pop1['costs'][vnf_id] != nfvi_pop2['costs'][vnf_id]
        else:
            m1 = map_unbalance2(nfvi_pop1['capabilities'],
                    nfvi_pop1['availableCapabilities'],
                    vnf_node['requirements']) 
            m2 = map_unbalance2(nfvi_pop2['capabilities'],
                    nfvi_pop2['availableCapabilities'],
                    vnf_node['requirements']) 
            res = m1 - m2

        return int(math.copysign(math.ceil(abs(res)), res))
    best_nfvi_pops.sort(cmp=which_is_better)

    return map(lambda nfvi_pop: nfvi_pop['id'], best_nfvi_pops)


# TODO - deprecated
def garrote_find_edge_path(ns_cluster, host_cluster, hosts_graph, vnfs_edge):
    """Finds a path to map VNF edges in the hosts graph. It is a
    Dijkstra shortest path accross host edges with tnough traffic resources.
    Note: VNFs must be already mapped to a host

    :ns_cluster: networkX graph instance with NS cluster
    :host_cluster: networkX graph instance with a host cluster
    :hosts_graph: networkX graph instance the the hosts
    :vnfs_edge: pair ('vnf_name1', 'vnf_name2')
    :returns: a list of hosts to map the vnfs_edge. Empty if no possible path:
    [('h1', 'h2'), ('h2', 'h5'), ...]

    """
    vnf_node1 = get_vnf(ns_cluster, vnfs_edge[0])
    vnf_node2 = get_vnf(ns_cluster, vnfs_edge[1])
    src_host = vnf_node1['place_at'][0] # TODO maybe more than one server
    req_traffic = ns_cluster[vnfs_edge[0]][vnfs_edge[1]]['traffic']

    ###=== Start Dijkstra
    dist, prev, Q = {}, {}, Set([])
    for host_name in host_cluster.nodes():
        dist[host_name] = sys.maxint
        prev[host_name] = sys.maxint
        Q.add(host_name)
    dist[src_host] = 0


    while len(Q) > 0:
        # Min distance node
        min_dis, u = sys.maxint, None
        for host_name in Q:
            if dist[host_name] < min_dis:
                min_dis, u = dist[host_name], host_name

        Q.remove(u)

        for v in host_cluster.neighbors(u):
            if hosts_graph[u][v]['free_capacity'] >= req_traffic:
                alt = dist[u] + hosts_graph[u][v]['delay']
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
    ###===end Dijkstra

    # Build up the list of traversed host edges
    curr_host = vnf_node2['place_at'][0]
    path = []
    while curr_host != vnf_node1['place_at'][0]:
        path.append((prev[curr_host], curr_host))
        curr_host = prev[curr_host]

    return path


def garrote_find_edge_path_mg(ns_cluster, nfvi_pop_cluster, nfvi_pops_graph,
        vnfs_edge):
    """Finds a path to map VNF edges in the nfvi_pops multi-graph. It is a
    Bellman Ford based path accross nfvi_pop edges with tnough traffic resources.
    Note: VNFs must be already mapped to a nfvi_pop

    :ns_cluster: networkX graph instance with NS cluster
    :nfvi_pop_cluster: networkX graph instance with a nfvi_pop cluster
    :nfvi_pops_graph: networkX graph instance the the nfvi_pops
    :vnfs_edge: triad ('vnf_id', 'vnf_id2', vl_key)
    :returns: a list of nfvi_pops to map the vnfs_edge. Empty if no possible path:
    [('NFVIPoP1', 'NFVIPoP2', key), ...]

    """
    
    vls, vl = get_vls(ns_cluster), None
    if vnfs_edge not in vls:
        vnfs_edge = (vnfs_edge[1], vnfs_edge[0], vnfs_edge[2])
    vl = get_vls(ns_cluster)[vnfs_edge]
    vnf1 = get_vnf(ns_cluster, vnfs_edge[0])
    vnf2 = get_vnf(ns_cluster, vnfs_edge[1])
    
    # Remove LLs with not enough bandwidth for the VLs
    nfvi_pops_graphC = nfvi_pops_graph.copy()
    lls = get_lls(nfvi_pop_cluster)
    for ll in lls:
        if lls[ll]['capacity']['available'] < vl['required_capacity'] or\
                lls[ll]['delay'] > vl['latency']:
            nfvi_pop1, nfvi_pop2, mLl = ll
            nfvi_pops_graphC.remove_edge(nfvi_pop1, nfvi_pop2, mLl)

    # Find with Bellman Ford the path
    pred, dist = nx.bellman_ford(nfvi_pops_graphC, vnf1['place_at'][0],
            weight='delay')

    # No path to the target NFVI PoP
    if vnf2['place_at'][0] not in pred or\
            dist[vnf2['place_at'][0]] > vl['latency']:
        return []

    currNFVIPoP = vnf2['place_at'][0]
    path = []
    while currNFVIPoP != None:
        prevNFVIPoP = pred[currNFVIPoP]

        mLlKey = None
        minWeight = float("inf")
        minBw = float("inf")

        # Get the one with minimum delay. With less BW if same delay
        for (nfvi_pop1, nfvi_pop2, mLl) in get_lls(nfvi_pops_graphC):
            if (prevNFVIPoP == nfvi_pop1 and currNFVIPoP == nfvi_pop2) or\
                    (prevNFVIPoP == nfvi_pop2 and currNFVIPoP == nfvi_pop1):
                delay = nfvi_pops_graphC[nfvi_pop1][nfvi_pop2][mLl]['delay']
                bw = nfvi_pops_graphC[nfvi_pop1][nfvi_pop2][mLl]\
['capacity']['available']

                if bw >= vl['required_capacity'] and minWeight >= delay and\
                        bw < minBw:
                    mLlKey = mLl
                    minWeight = delay
                    minBw = bw

        if prevNFVIPoP != None:
            path = [(prevNFVIPoP, currNFVIPoP, mLlKey)] + path
        currNFVIPoP = prevNFVIPoP

    return path


def garrote_ns_mapping(pa_req, ns_cluster, nfvi_pop_cluster, nfvi_pops_graph,
        ns_cl_name=None, nfvi_pop_cl_name=None):
    """Maps all VNFs inside the NS cluster to the NFVI PoPs cluster. Changes 
    are reflected in the pa_req PARequest JSON and inside the nfvi_pops_graph

    :pa_req: API PARequest dictionary
    :ns_cluster: networkX multi-graph instance with NS cluster
    :nfvi_pop_cluster: networkX multi-graph instance with a NFVI PoPs cluster
    :nfvi_pops_graph: networkX multi-graph instance the hosts
    :ns_cl_name: name of the ns_cluster
    :nfvi_pop_cl_name: name of the host_cl
    :returns: a PARequest JSON extended with mapping decisions
              and a boolean telling if mapping worked (True/False)

    """
    mappings = {'vnf': {}, 'link': {}}

    # Map VNF to hosts
    for vnf_id in ns_cluster.nodes():
        best_nfvi_pops = garrote_best_vnf_nfvi_pops(
            pa_req,
            get_vnf(ns_cluster, vnf_id),
            nfvi_pop_cluster,
            nfvi_pops_graph
        )
        if not best_nfvi_pops:
            print '  !!ERR: cannot map vnf=' + vnf_id +\
                ' when mapping ns_cluster=' + str(ns_cl_name) +\
                ' into nfvi_pop_cluster=' + str(nfvi_pop_cl_name)
            return pa_req, False
        map_vnf(ns_cluster, nfvi_pops_graph, vnf_id, best_nfvi_pops[0])
        mappings['vnf'][vnf_id] = best_nfvi_pops[0]
        for i in range(len(pa_req['nsd']['VNFs'])):
            if pa_req['nsd']['VNFs'][i]['VNFid'] == vnf_id:
                pa_req['nsd']['VNFs'][i]['place_at'].insert(0,
                        best_nfvi_pops[0])
                print "   VNF " + pa_req['nsd']['VNFs'][i]['VNFid'] + " --  host " + best_nfvi_pops[0]

        for i in range(len(pa_req['nfvi']['NFVIPoPs'])):
            if pa_req['nfvi']['NFVIPoPs'][i]['id'] == best_nfvi_pops[0]:
                pa_req['nfvi']['NFVIPoPs'][i]['mappedVNFs'].insert(0, vnf_id)

    # Map VNF edges to host edges
    for vl in get_vls(ns_cluster):
        nfvi_pops_path = garrote_find_edge_path_mg(ns_cluster,
                nfvi_pop_cluster, nfvi_pops_graph, vl)
        map_vnfs_edge(ns_cluster, nfvi_pops_graph, vl, nfvi_pops_path)
        persist_vnf_path_map(pa_req, nfvi_pops_graph, ns_cluster, vl,
                nfvi_pops_path)

    return pa_req, True


def garrote_mapping(pa_req, legacy_reqs):
    """Maps the VNFs present in the pa_req to underlying hosts and network
    links.

    :pa_req: API PARequest dictionary
    :legacy_reqs: a list of previous requests with the same underlying NFVI as
    the pa_req parameter
    :returns: a API PARequest extended with mapping decisions
              and a boolean telling if the mapping worked

    """
    # Cluster matching
    pa_req, worked = garrote_matching(pa_req, legacy_reqs)
    if not worked:
        return pa_req, False
    

    # From here on is about VNF mapping
    ns_graph = create_ns_graph(pa_req)
    ns_clusters = create_ns_clusters([pa_req]) 
    # ns_clusters = create_ns_list(pa_req) - TODO not used?
    nfvi_pop_clusters = create_nfvi_pop_clusters(pa_req)
    nfvi_pop_graph = create_nfvi_pop_graph(pa_req)

    # Perform intra cluster mapping
    for ns_cl_name in ns_clusters:
        ns_cluster = ns_clusters[ns_cl_name]
        vnf_node = get_vnf(ns_graph, list(ns_cluster.nodes())[0])
        nfvi_pop_cluster = nfvi_pop_clusters[vnf_node['nfviPoPCluster']]
        print "ns_cl:" + ns_cl_name + " <--> nfvi_cl:" + vnf_node['nfviPoPCluster']
        pa_req, map_worked = garrote_ns_mapping(pa_req, ns_cluster,
            nfvi_pop_cluster, nfvi_pop_graph, ns_cl_name, vnf_node['cluster'])
        if not map_worked:
            return pa_req, False

    # Perform inter cluster links mapping
    inter_cluster_vl = get_inter_cluster_vl(ns_graph)
    for vnfs_edge in inter_cluster_vl:
        nfvi_pops_path = garrote_find_edge_path_mg(ns_graph, nfvi_pop_graph,
                nfvi_pop_graph, vnfs_edge)
        map_vnfs_edge(ns_graph, nfvi_pop_graph, vnfs_edge, nfvi_pops_path)
        persist_vnf_path_map(pa_req, nfvi_pop_graph, ns_graph, vnfs_edge,
                nfvi_pops_path)

    # Check if all NS' simple paths are below max_latency
    if 'max_latency' in pa_req['nsd']:
        if not ns_mapping_below_latency(pa_req, ns_graph):
            return pa_req, False

    # For testing purpose
    with open('/tmp/finish_req.json', 'w') as tmp:
        json.dump(pa_req, tmp, indent=4)

    return pa_req, True


# TODO
def garrote_fast_check(scenario):
    """Checks if the mapping decisions satisfy the service requirements.

    :scenario: PIMRC18 JSON model with mapping performed by garrote heuristic
    :returns: PIMRC18 JSON dict extended with
              {'service_name': 's', 'map_ok': 'yes/no'}

    """
    pass


def best_garrote(pa_req):
    """Executes garrota algorithm through every clustering possibility and
    returns the best one.

    :pa_req: PA request dictionary with the multiple clustering decisions made
    by the agglomerative clustering
    :returns: PA response with for the best clustering or None if it is
    impossible

    """
    best_cost, best_mapping = sys.maxint, None

    heat_wood(pa_req)
    with open('/tmp/vl-sap.json', 'w') as tmp:
        json.dump(pa_req, tmp, indent=4)
    for clust_idx in range(len(pa_req['clustering_decisions'])):
        pa_req_ = copy.deepcopy(pa_req)
        integrate_decisions(pa_req_, clust_idx)
        pa_req_, worked = garrote_mapping(pa_req_, [])
        print "worked=" + str(worked)
        with open('/tmp/cluster-' + str(clust_idx) + '-map.json', 'w') as tmp:
            json.dump(pa_req_, tmp, indent=4)


        if worked:
            mapped_cost = mapping_cost(pa_req_)
            pa_req_['totalCost'] = mapped_cost
            print "cost = " + str(mapped_cost)

            if best_cost > mapped_cost:
                print "BEST option => " + str(clust_idx + 1) + " clusters"
                best_mapping = pa_req_
                best_cost = mapped_cost

        print "\n"

    return result2PAResponse(best_mapping)


