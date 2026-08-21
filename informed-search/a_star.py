from typing import List
import heapq

class Node:
    def __init__(self, position, parent=None, g=0, h=0):
        self.position = position
        self.parent = parent
        self.g = g  # Cost from start node
        self.h = h  # Heuristic (estimated cost to goal)
        self.f = g + h  # Total estimated cost

    def __lt__(self, other):
        return self.f < other.f  # Min-heap (lowest f(n) first)

def heuristic(start, goal):
    """Manhattan Distance heuristic"""
    return abs(start[0] - goal[0]) + abs(start[1] - goal[1])

def solve(grid, start, goal):
    open_set = []
    heapq.heappush(open_set, Node(start, None, 0, heuristic(start, goal)))

    closed_set = set()
    node_map = {start: Node(start, None, 0, heuristic(start, goal))}

    while open_set:
        current = heapq.heappop(open_set)

        if current.position == goal:
            path = []
            while current:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Reverse path to start → goal

        closed_set.add(current.position)

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Left, Right, Up, Down
            neighbor_pos = (current.position[0] + dx, current.position[1] + dy)

            # Check if within grid bounds and not an obstacle
            if (0 <= neighbor_pos[0] < len(grid)) and (0 <= neighbor_pos[1] < len(grid[0])) and grid[neighbor_pos[0]][neighbor_pos[1]] == 0 and neighbor_pos not in closed_set:
                g_cost = current.g + 1
                h_cost = heuristic(neighbor_pos, goal)

                neighbor = Node(neighbor_pos, current, g_cost, h_cost)

                if neighbor_pos not in node_map or g_cost < node_map[neighbor_pos].g:
                    heapq.heappush(open_set, neighbor)
                    node_map[neighbor_pos] = neighbor

    return None  # No path found

# Example Grid (0 = open, 1 = obstacle)
grid = [
    [0, 1, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0]
]

start = (0, 0)
goal = (4, 4)

path = solve(grid, start, goal)
print("Path:", path)
