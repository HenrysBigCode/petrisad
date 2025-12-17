import networkx as nx
from collections import deque
from logic.petri_net import PetriNet

# --- PARTIE 1 : VISUALISATION ---
class StateSpaceVisualizer:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_state(self, state_id, marking_data, is_deadlock=False, is_initial=False):
        label = str(marking_data)
        color = 'lightgray'
        if is_initial: color = '#90EE90'
        elif is_deadlock: color = '#FF7F7F'
        self.graph.add_node(state_id, label=label, color=color, full_data=marking_data)

    def add_transition(self, source_id, target_id, transition_name):
        self.graph.add_edge(source_id, target_id, label=transition_name)

# --- PARTIE 2 : UTILITAIRES ---
def get_marking(net: PetriNet):
    return tuple(p.tokens for p in net.places.values())

def apply_marking(net: PetriNet, marking):
    for place, value in zip(net.places.values(), marking):
        place.tokens = value
        
def format_marking(net: PetriNet, marking):
    return "\n".join(f"{p.name}: {value}" for p, value in zip(net.places.values(), marking))

def simulate_fire(net: PetriNet, t):
    """Simule manuellement le tir d'une transition sans dépendre de fire_transition."""
    for arc in net.arcs:
        if arc.transition == t and arc.direction == "place_to_transition":
            arc.place.tokens -= arc.weight
        elif arc.transition == t and arc.direction == "transition_to_place":
            arc.place.tokens += arc.weight

# --- PARTIE 3 : ALGORITHMES ---
def build_state_space(net: PetriNet, visualizer: StateSpaceVisualizer):
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
            simulate_fire(net, t) # Utilisation de la simulation manuelle
            m_target = get_marking(net)
            if m_target not in seen:
                target_id = next_id
                seen[m_target] = target_id
                visualizer.add_state(target_id, format_marking(net, m_target))
                queue.append(m_target)
                next_id += 1
            else:
                target_id = seen[m_target]
            visualizer.add_transition(source_id, target_id, t.name)
            apply_marking(net, m_source)
    apply_marking(net, initial_marking)

def checkVivacity(net: PetriNet):
    initial_tokens = {name: p.tokens for name, p in net.places.items()}
    start_marking = get_marking(net)
    visited = {start_marking}
    queue = deque([start_marking])
    fired_transitions = set()
    deadlock_found = False

    while queue and len(visited) < 1000:
        curr = queue.popleft()
        apply_marking(net, curr)
        enabled = net.get_enabled()
        if not enabled: 
            deadlock_found = True
        for t in enabled:
            fired_transitions.add(t.name)
            simulate_fire(net, t) # Correction ici aussi
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