# logic/analisis.py TO BE TESTED and modified

from logic.petri_net import PetriNet

# return True si le réseau est en deadlock
def is_deadlocked(net: PetriNet):
    return len(net.get_enabled()) == 0

def checkLoop(self):
    """
    Détecte s'il existe une boucle structurelle (cycle) dans le réseau de Petri.
    Retourne True si une boucle est trouvée, False sinon.
    """
    # construction du graphe (liste d'adjacence)
    # on associe chaque objet (Place ou Transition) à ses voisins aval
    adj = {}

    # initialiser les entrées pour tous les nœuds
    for p in self.places.values():
        adj[p] = []
    for t in self.transitions.values():
        adj[t] = []

    # remplir les voisins en fonction des arcs
    for arc in self.arcs:
        if arc.direction == 'place_to_transition':
            adj[arc.place].append(arc.transition)
        elif arc.direction == 'transition_to_place':
            adj[arc.transition].append(arc.place)

    # algorithme de détection de cycle (DFS)
    visited = set()   
    recursion_stack = set() 

    def dfs(node):
        visited.add(node)
        recursion_stack.add(node)

        # explorer les voisins
        for neighbor in adj[node]:
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in recursion_stack:
                # si le voisin est dans la pile de récursion actuelle c'est une boucle
                return True

        # on retire le noeud du chemin actuel
        recursion_stack.remove(node)
        return False

    # lancer le DFS sur tous les noeuds
    all_nodes = list(self.places.values()) + list(self.transitions.values())
        
    for node in all_nodes:
        if node not in visited:
            if dfs(node):
                print(f"Cycle détecté impliquant : {node.name}")
                return True
        
    return False


def getLoop(self):
    """
    Retourne la liste des nœuds [Place, Transition, ...] formant une boucle.
    Retourne une liste vide [] s'il n'y a pas de boucle.
    """
    adj = {}
    for p in self.places.values(): adj[p] = []
    for t in self.transitions.values(): adj[t] = []
    for arc in self.arcs:
        if arc.direction == 'place_to_transition':
            adj[arc.place].append(arc.transition)
        else:
            adj[arc.transition].append(arc.place)

    visited = set()
    recursion_stack = [] 

    def dfs(node):
        visited.add(node)
        recursion_stack.append(node)

        for neighbor in adj[node]:
            if neighbor not in visited:
                result = dfs(neighbor)
                if result: return result
            elif neighbor in recursion_stack:
                loop_start_index = recursion_stack.index(neighbor)
                return recursion_stack[loop_start_index:]

        recursion_stack.pop()
        return None

    all_nodes = list(self.places.values()) + list(self.transitions.values())
    for node in all_nodes:
        if node not in visited:
            cycle_path = dfs(node)
            if cycle_path:
                return cycle_path 
        
    return []

    
    
def checkVivacity(self):
    """
    Analyse la vivacité du réseau en simulant son exécution.
    Retourne : 0 (Mort/Deadlock), 1 (Vivant faible), 2 (Vivant parfait)
    """
    # sauvegarder l'état initial des jetons pour remettre propre à la fin
    initial_tokens = {p_name: p.tokens for p_name, p in self.places.items()}
    
    # état = tuple trié (Place, nb_jetons) pour être unique et hashable
    start_state = tuple(sorted((p, self.places[p].tokens) for p in self.places))
    
    visited_states = {start_state}
    queue = [start_state]
    fired_transitions = set()
    
    max_states = 1000 
    steps = 0
    deadlock_found = False

    while queue and steps < max_states:
        current_state_tuple = queue.pop(0)
        steps += 1
        
        # restaurer l'état (les jetons) pour tester les chemins depuis ici
        for p_name, tokens in current_state_tuple:
            self.places[p_name].tokens = tokens
            
        # récupérer les transitions activables
        enabled_transitions = self.get_enabled()
        
        # détection de deadlock
        if not enabled_transitions:
            deadlock_found = True
        
        # simuler les tirs pour chaque possibilité
        for t in enabled_transitions:
            fired_transitions.add(t.name)

            arcs_entrants = [a for a in self.arcs if a.transition == t and a.direction == "place_to_transition"]
            arcs_sortants = [a for a in self.arcs if a.transition == t and a.direction == "transition_to_place"]
            
            t.fire(arcs_entrants, arcs_sortants)
            
            # capturer le nouvel état
            new_state = tuple(sorted((p, self.places[p].tokens) for p in self.places))
            
            if new_state not in visited_states:
                visited_states.add(new_state)
                queue.append(new_state)
            
            # remettre les jetons comme avant le tir pour tester le prochain voisin
            for p_name, tokens in current_state_tuple:
                self.places[p_name].tokens = tokens

    # restaurer l'état initial complet du réseau
    for p_name, t_count in initial_tokens.items():
        self.places[p_name].tokens = t_count

    if deadlock_found:
        return 0 
    
    all_transitions = set(self.transitions.keys())
    if fired_transitions == all_transitions:
        return 2 
    else:
        return 1 
    
"""
def checkBoundedness(self):
    # Placeholder for boundedness detection logic
    pass

def get_marking(net): #????
    "Return marking as a tuple for hashing."
    return tuple(p.tokens for p in net.places.values())


def reachable_markings(net): #????
    "Compute reachable markings using BFS."
    from collections import deque

    seen = set()
    queue = deque()

    initial = get_marking(net)
    queue.append(initial)
    seen.add(initial)

    while queue:
        marking = queue.popleft()

        # apply marking
        for place, value in zip(net.places.values(), marking):
            place.tokens = value

        enabled = net.get_enabled()
        for t in enabled:
            inc = net.get_incoming(t)
            out = net.get_outgoing(t)

            # simulate fire
            for arc in inc:
                arc.place.tokens -= arc.weight
            for arc in out:
                arc.place.tokens += arc.weight

            new_marking = get_marking(net)

            # undo (restore original marking)
            for place, value in zip(net.places.values(), marking):
                place.tokens = value

            if new_marking not in seen:
                seen.add(new_marking)
                queue.append(new_marking)

    return seen

"""

PetriNet.checkLoop = checkLoop
PetriNet.getLoop = getLoop
PetriNet.checkVivacity = checkVivacity


def print_vivacity_result(level):
    if level == 0:
        print(f"-> Résultat : {level} (DEADLOCK - Le réseau va se bloquer)")
    elif level == 1:
        print(f"-> Résultat : {level} (FAIBLE - Tourne, mais transitions inutilisées)")
    elif level == 2:
        print(f"-> Résultat : {level} (VIVANT - Tout fonctionne parfaitement)")

if __name__ == "__main__":
    print("=== DÉDUT DES TESTS DE BOUCLE ===")

    """
    # ---------------------------------------------------------
    # Cas 1 : Réseau sans boucle (Ligne droite)
    # P1 -> T1 -> P2
    # ---------------------------------------------------------

    print("Test 1")
    net1 = PetriNet()
    net1.add_place("P1")
    net1.add_place("P2")
    net1.add_transition("T1")
    net1.add_arc("P1", "T1")
    net1.add_arc("T1", "P2")

    if net1.checkLoop() == False:
        print("[SUCCESS] Test 1 (Pas de boucle) : OK")
    else:
        print("[FAILURE] Test 1 : Erreur, une boucle a été trouvée alors qu'il n'y en a pas.")

    # ---------------------------------------------------------
    # Cas 2 : Réseau avec boucle simple
    # P1 <-> T1
    # ---------------------------------------------------------
        
    print("Test 2")
    net2 = PetriNet()
    net2.add_place("P1")
    net2.add_transition("T1")
    net2.add_arc("P1", "T1")
    net2.add_arc("T1", "P1") 

    if net2.checkLoop() == True:
        print("[SUCCESS] Test 2 (Boucle simple) : OK")
        loop = net2.getLoop()
        if loop:
            print(f"       -> Chemin trouvé : {' -> '.join([n.name for n in loop])} -> {loop[0].name}")
    else:
        print("[FAILURE] Test 2 : Erreur, la boucle n'a pas été détectée.")

    # ---------------------------------------------------------
    # Cas 3 : Boucle plus complexe
    # P1 -> T1 -> P2 -> T2 -> P1
    # ---------------------------------------------------------
        
    print("Test 3")
    net3 = PetriNet()
    net3.add_place("P1")
    net3.add_place("P2")
    net3.add_transition("T1")
    net3.add_transition("T2")

    net3.add_arc("P1", "T1")
    net3.add_arc("T1", "P2")
    net3.add_arc("P2", "T2") 
    net3.add_arc("T2", "P1") # Retour vers P1 (boucle)

    if net3.checkLoop() == True:
        print("[SUCCESS] Test 3 (Boucle complexe) : OK")
        loop = net3.getLoop()
        if loop:
            print(f"       -> Chemin trouvé : {' -> '.join([n.name for n in loop])} -> {loop[0].name}")
    else:
        print("[FAILURE] Test 3 : Erreur, la boucle complexe n'a pas été détectée.")

    print("=== FIN DES TESTS ===")
    """
    


    print("=== TESTS VIVACITÉ AVEC is_deadlocked ===")

    # CAS 1 : Deadlock
    print("\n[TEST 1] Réseau qui se bloque")
    net1 = PetriNet()
    net1.add_place("P1"); net1.places["P1"].tokens = 1
    net1.add_place("P2")
    net1.add_transition("T1")
    net1.add_arc("P1", "T1")
    net1.add_arc("T1", "P2") # P2 absorbe le jeton, plus rien ne sort
    
    lvl = net1.checkVivacity()
    print_vivacity_result(lvl) # Attendu : 0

    # CAS 2 : Vivant Parfait
    print("\n[TEST 2] Réseau parfaitement vivant (Cycle)")
    net2 = PetriNet()
    net2.add_place("P1"); net2.places["P1"].tokens = 1
    net2.add_place("P2")
    net2.add_transition("T1"); net2.add_transition("T2")
    net2.add_arc("P1", "T1"); net2.add_arc("T1", "P2")
    net2.add_arc("P2", "T2"); net2.add_arc("T2", "P1")

    lvl = net2.checkVivacity()
    print_vivacity_result(lvl) # Attendu : 2