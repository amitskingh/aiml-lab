import heapq


class Graph:
    def __init__(self):
        self.adjacency_list = {}

    def add_edge(self, node, neighbor, cost=1):
        if node not in self.adjacency_list:
            self.adjacency_list[node] = []
        if neighbor not in self.adjacency_list:
            self.adjacency_list[neighbor] = []
        self.adjacency_list[node].append((neighbor, cost))
        self.adjacency_list[neighbor].append(
            (node, cost))  # Assuming an undirected graph


def best_first_search(graph, start, goal, heuristic):
    priority_queue = []
    # Push (heuristic, node)
    heapq.heappush(priority_queue, (heuristic[start], start))
    visited = set()
    parent = {start: None}  # Track the path

    while priority_queue:
        _, current = heapq.heappop(priority_queue)

        if current in visited:
            continue

        visited.add(current)

        # Goal check
        if current == goal:
            return reconstruct_path(parent, goal)

        for neighbor, _ in graph.adjacency_list.get(current, []):
            if neighbor not in visited:
                heapq.heappush(priority_queue, (heuristic[neighbor], neighbor))
                parent[neighbor] = current

    return None  # No path found


def reconstruct_path(parent, current):
    path = []
    while current is not None:
        path.append(current)
        current = parent[current]
    return path[::-1]  # Reverse to get correct order


graph = Graph()
edges = [
    ('A', 'B', 1), ('A', 'C', 3), ('B', 'D', 4),
    ('B', 'E', 2), ('C', 'F', 5), ('E', 'G', 1),
    ('F', 'G', 3)
]

for u, v, cost in edges:
    graph.add_edge(u, v, cost)

# Heuristic function (Estimated distance to goal G)
heuristic = {
    'A': 6, 'B': 4, 'C': 4, 'D': 6,
    'E': 2, 'F': 3, 'G': 0
}

# Run Best First Search
start, goal = 'A', 'G'
path = best_first_search(graph, start, goal, heuristic)

print("Best First Search Path:", path)
