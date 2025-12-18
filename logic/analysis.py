# logic/analysis.py
# Module pour l'analyse et la visualisation de l'espace d'états d'un réseau de Petri

import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
from logic.petri_net import PetriNet

# Classe pour visualiser l'espace d'états
class StateSpaceVisualizer:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_state(self, state_id, marking_data, is_deadlock=False, is_initial=False):
        # On entoure le label de guillemets pour éviter l'erreur pydot ":"
        label = f'"{marking_data}"'
        
        color = 'lightgray'
        if is_initial: 
            color = '#90EE90'
        elif is_deadlock: 
            color = '#FF7F7F'

        self.graph.add_node(state_id, label=label, color=color, full_data=marking_data)

    def add_transition(self, source_id, target_id, transition_name):
        self.graph.add_edge(source_id, target_id, label=transition_name)

    def show_interactive(self):
        """Displays the graph in a popup window using the Tree layout"""
        node_labels = nx.get_node_attributes(self.graph, 'label')
        
        BASE_NODE_SIZE = 1500  
        SIZE_PER_CHAR = 180    
        node_sizes = [BASE_NODE_SIZE + len(node_labels.get(n, '')) * SIZE_PER_CHAR for n in self.graph.nodes]

        try:
            # Try to use Graphviz for Tree layout
            from networkx.drawing.nx_pydot import graphviz_layout
            pos = graphviz_layout(self.graph, prog='dot')
        except Exception as e:
            # Fallback if Graphviz is not installed
            print(f"Graphviz not found, using shell layout. Error: {e}")
            pos = nx.shell_layout(self.graph)

        plt.figure(figsize=(12, 10))
        colors = [data['color'] for node, data in self.graph.nodes(data=True)]
        
        nx.draw_networkx_nodes(self.graph, pos, node_color=colors, node_size=node_sizes, edgecolors='black')
        nx.draw_networkx_labels(self.graph, pos, labels=node_labels, font_size=9)
        nx.draw_networkx_edges(self.graph, pos, arrows=True, arrowsize=20, 
                               connectionstyle='arc3, rad=0.1', edge_color='gray')
        
        edge_labels = nx.get_edge_attributes(self.graph, 'label')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='blue')

        plt.title("Espace d'États")
        plt.axis('off') 
        plt.show()

# fonctions utilitaires pour l'analyse
def get_marking(net: PetriNet):
    return tuple(p.tokens for p in net.places.values())

def apply_marking(net: PetriNet, marking):
    for place, value in zip(net.places.values(), marking):
        place.tokens = value
        
def format_marking(net: PetriNet, marking):
    # On remplace ":" par "=" pour éviter tout conflit avec pydot
    return "\n".join(f"{p.name}={value}" for p, value in zip(net.places.values(), marking))

def simulate_fire(net: PetriNet, t):
    for arc in net.arcs:
        if arc.transition == t and arc.direction == "place_to_transition":
            arc.place.tokens -= arc.weight
        elif arc.transition == t and arc.direction == "transition_to_place":
            arc.place.tokens += arc.weight

def build_state_space(net: PetriNet, visualizer: StateSpaceVisualizer):
    # FORCE le marquage actuel sur le marquage initial pour la simulation
    for p in net.places.values():
        p.tokens = p.initial_tokens if hasattr(p, 'initial_tokens') and p.tokens == 0 else p.tokens

    seen = {}
    queue = deque()       
    next_id = 0
    
    initial_marking = get_marking(net)
    seen[initial_marking] = next_id
    visualizer.add_state(next_id, format_marking(net, initial_marking), is_initial=True)
    queue.append(initial_marking)
    next_id += 1

    while queue:
        m_source = queue.popleft()
        source_id = seen[m_source]
        apply_marking(net, m_source) 

        enabled = net.get_enabled()
        if not enabled:
            visualizer.graph.nodes[source_id]['color'] = '#FF7F7F'

        for t in enabled:
            simulate_fire(net, t)
            m_target = get_marking(net)
            
            if m_target not in seen:
                target_id = next_id
                seen[m_target] = target_id
                visualizer.add_state(target_id, format_marking(net, m_target))
                queue.append(m_target)
                next_id += 1
            else:
                target_id = seen[m_target]
            
            visualizer.graph.add_edge(source_id, target_id, label=t.name)
            apply_marking(net, m_source) 
            
    apply_marking(net, initial_marking)

# algrithmes de verification des propriétés
def checkVivacity(net: PetriNet):
    start_marking = get_marking(net)
    visited = {start_marking}
    queue = deque([start_marking])
    fired_transitions = set()
    deadlock_found = False

    while queue and len(visited) < 1000:
        curr = queue.popleft()
        apply_marking(net, curr)
        enabled = net.get_enabled()
        if not enabled: deadlock_found = True
        for t in enabled:
            fired_transitions.add(t.name)
            simulate_fire(net, t)
            new_m = get_marking(net)
            if new_m not in visited:
                visited.add(new_m)
                queue.append(new_m)
            apply_marking(net, curr)

    apply_marking(net, start_marking)
    if deadlock_found: return 0
    return 2 if len(fired_transitions) == len(net.transitions) else 1

def checkLoop(net: PetriNet):
    adj = {n: [] for n in list(net.places.values()) + list(net.transitions.values())}
    for arc in net.arcs:
        if arc.direction == 'place_to_transition':
            adj[arc.place].append(arc.transition)
        else:
            adj[arc.transition].append(arc.place)
    visited, stack = set(), set()
    def dfs(node):
        visited.add(node)
        stack.add(node)
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor): return True
            elif neighbor in stack: return True
        stack.remove(node)
        return False
    for node in adj:
        if node not in visited:
            if dfs(node): return True
    return False