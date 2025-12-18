import networkx as nx
import matplotlib.pyplot as plt
import pydot
from collections import deque
from logic.petri_net import PetriNet, Transition, Place

class StateSpaceVisualizer:
    def __init__(self):
        self.graph = nx.DiGraph() # Graphe orienté

    def add_state(self, state_id, marking_data, is_deadlock=False, is_initial=False):

        # Formatter le label pour qu'il ne soit pas trop long
        label = f'"{marking_data}"'
        
        color = 'lightgray' # Couleur de base
        if is_initial: 
            color = '#90EE90' # Point initial
        elif is_deadlock: 
            color = '#FF7F7F' # Deadlock

        self.graph.add_node(state_id, label=label, color=color, full_data=marking_data)

    def add_transition(self, source_id, target_id, transition_name):
        self.graph.add_edge(source_id, target_id, label=transition_name)

    def show_interactive(self):
        

        node_labels = nx.get_node_attributes(self.graph, 'label')
        
        # Paramètres d'ajustement taille des noeuds
        BASE_NODE_SIZE = 1200  
        SIZE_PER_CHAR = 150    
        
        node_sizes = []
        for node_id in self.graph.nodes:
            label = node_labels.get(node_id, '')
            
            #
            size = BASE_NODE_SIZE + len(label) * SIZE_PER_CHAR
            node_sizes.append(size)

        try:
            # Création d'un arbre hierarchique
            pos = nx.nx_pydot.graphviz_layout(self.graph, prog='dot')

        except Exception as e:
            # Si Graphviz n'est pas installé
            print(f"Erreur : {e}")
            pos = nx.spring_layout(self.graph)

        num_nodes = len(self.graph.nodes)
        
        # Définir une taille de base et l'adapter
        base_width = 10
        base_height = 6
        
        # Ajuster la taille de la fenetre avec un coefficient
        scale_factor = max(1, num_nodes ** 0.5 / 2.0)
        
        # Définir la taille finale de la figure
        fig_width = base_width * scale_factor
        fig_height = base_height * scale_factor
        
        plt.figure(figsize=(fig_width, fig_height))
        
        
        # Récupérer les couleurs des noeuds
        colors = [data['color'] for node, data in self.graph.nodes(data=True)]
        
        # Création de nodes
       
        nx.draw_networkx_nodes(self.graph, pos, node_color=colors, node_size=node_sizes, edgecolors='black')
        
        # Label
        labels = nx.get_node_attributes(self.graph, 'label')

  

        nx.draw_networkx_labels(self.graph, pos, labels=labels, font_size=10)
        
        # Arretes
 
        nx.draw_networkx_edges(self.graph, pos, arrows=True, arrowsize=20, node_size=node_sizes)
        
        # label des arretes
        edge_labels = nx.get_edge_attributes(self.graph, 'label')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='blue')

        plt.title("Visualisation de l'Espace d'États (Test)")
        plt.margins(0.15)
        plt.axis('off') 
        plt.show() #ouvrir le pop up

# Fonctions d'aide pour la gestion des marquages

def get_marking(net: PetriNet):

    #Retourne le marquage actuel comme un tuple pour le hachage

    return tuple(p.tokens for p in net.places.values()) 

def apply_marking(net: PetriNet, marking):

    #Applique un marquage donné

    for place, value in zip(net.places.values(), marking):
        place.tokens = value
        
def format_marking(net: PetriNet, marking):
    #Formate le marquage pour l'affichage
    return "\n".join(f"{p.name}: {value}" for p, value in zip(net.places.values(), marking))

def build_state_space(net: PetriNet, visualizer: StateSpaceVisualizer):
    
    #Construit le graphe d'espace d'état à l'aide de BFS
    
    # suivi
    seen = {}
    queue = deque()       
    next_id = 0
    
   #initialisation
    initial_marking = get_marking(net)
    
    current_id = next_id
    next_id += 1
    seen[initial_marking] = current_id
    queue.append(initial_marking)


    visualizer.add_state(
        state_id=current_id, 
        marking_data=format_marking(net, initial_marking), 
        is_initial=True
    )

    # BFS
    while queue:
        M_source = queue.popleft()
        source_id = seen[M_source]

        # Appliquer le marquage source 
        apply_marking(net, M_source) 

        enabled = net.get_enabled()
        
        #Deadlocks
        if not enabled:

            visualizer.graph.nodes[source_id]['color'] = '#FF7F7F' # Rouge
            
        # Simulation du tir
        for t in enabled:       
            
            arcs_entrants = net.get_arcs_entrants(t)
            for arc in arcs_entrants:
                arc.place.tokens -= arc.weight
            
            arcs_sortants = net.get_arcs_sortants(t)
            for arc in arcs_sortants:
                arc.place.tokens += arc.weight

            # Marquage M_target
            M_target = get_marking(net)
            
            #Gestion de l'état cible

            if M_target not in seen:
                # Si nouvelle état alors ajouter
                target_id = next_id
                next_id += 1
                seen[M_target] = target_id
                queue.append(M_target)

                # Ajouter au visualiseur
                visualizer.add_state(
                    state_id=target_id, 
                    marking_data=format_marking(net, M_target)
                )
            else:
                target_id = seen[M_target]
            
            # 6. Ajouter l'Arc
            visualizer.add_transition(source_id, target_id, t.name)
            
            # Reinitialisation
            apply_marking(net, M_source) 
            
    # Reset
    apply_marking(net, initial_marking)


#Partie Test
'''
if __name__ == "__main__":
    print("Démarrage du test de visualisation avec moteur...")


    # Création d'un réseau de Pétri 
    net = PetriNet()
    p1 = net.add_place("P1")
    p2 = net.add_place("P2")
    p3 = net.add_place("P3")
    p4 = net.add_place("P4")
    p5 = net.add_place("P5")
    p6 = net.add_place("P6")
    t1 = net.add_transition("t1")
    t2 = net.add_transition("t2")
    t3 = net.add_transition("t3")
    t4 = net.add_transition("t4")
    t5 = net.add_transition("t5")
    t6 = net.add_transition("t6")
    
    # Marquage initial
    net.set_tokens("P1", 1) 
    net.set_tokens("P2", 0) 
    net.set_tokens("P3",0)
    net.set_tokens("P4", 0) 
    net.set_tokens("P5",0)
    net.set_tokens("P6",0)

    
    # Arcs
    net.add_arc("P1", "t1") # P1 -> t1
    net.add_arc("t1", "P2") # t1 -> P2
    net.add_arc("P2", "t2") # P2 -> t2
    net.add_arc("t2", "P3") # t2 -> P1
    net.add_arc("P1", "t3") # P1 -> t3
    net.add_arc("t3", "P3") # t3 -> P3
    net.add_arc("P2", "t4") # P2 -> t2
    net.add_arc("t4", "P4") # t2 -> P1
    net.add_arc("P2", "t5") # P1 -> t3
    net.add_arc("t5", "P5") # t3 -> P3
    net.add_arc("P4", "t6") # P1 -> t3
    net.add_arc("t6", "P6") # t3 -> P3

    viz = StateSpaceVisualizer()

    print("Construction du graphe d'accessibilité...")
    build_state_space(net, viz)

    print("Affichage du graphe...")
    viz.show_interactive()
    print("Test terminé.")

    '''