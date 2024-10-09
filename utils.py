from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def optimize_route(appointments):
    if not appointments:
        return []

    # Create a distance matrix
    locations = [(app.latitude, app.longitude) for app in appointments]
    num_locations = len(locations)
    distances = {}
    for from_node in range(num_locations):
        distances[from_node] = {}
        for to_node in range(num_locations):
            if from_node == to_node:
                distances[from_node][to_node] = 0
            else:
                distances[from_node][to_node] = calculate_distance(locations[from_node], locations[to_node])

    # Create routing model
    manager = pywrapcp.RoutingIndexManager(num_locations, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distances[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Set first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Get the optimized route
    optimized_route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node_index = manager.IndexToNode(index)
        optimized_route.append({
            'lat': locations[node_index][0],
            'lng': locations[node_index][1],
            'client_name': appointments[node_index].client_name,
            'address': appointments[node_index].address,
            'appointment_time': appointments[node_index].appointment_time.isoformat()
        })
        index = solution.Value(routing.NextVar(index))

    return optimized_route

def calculate_distance(loc1, loc2):
    # Simple Euclidean distance for demonstration
    # In a real-world scenario, you'd use a more accurate distance calculation or a mapping API
    return ((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)**0.5
