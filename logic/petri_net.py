# logic/petri_net.py test

# Représente une place dans le réseau de Petri
class Place:
    def __init__(self, name):
        self.name = name
        self.initial_tokens = 0
        self.tokens = 0

    # Impression débug pour une place
    def __repr__(self):
        return f"Place({self.name}, tokens={self.tokens})"


# Représente une transition dans le réseau de Petri
class Transition:
    def __init__(self, name):
        self.name = name

    # Impression débug pour une transition
    def __repr__(self):
        return f"Transition({self.name})"

    # Vérifie si la transition est tirable
    def is_enabled(self, arcs_entrants):
        return all(arc.place.tokens >= arc.weight for arc in arcs_entrants)


# Représente un arc reliant une place à une transition ou vice-versa
class Arc:
    def __init__(self, place, transition, direction, weight=1):
        # Check si on créé un arc avec une direction valide, should never be needed
        if direction not in ['place_to_transition', 'transition_to_place']:
            raise ValueError("La direction de l'arc doit être 'place_to_transition' ou 'transition_to_place'")
            
        self.place = place
        self.transition = transition
        self.direction = direction
        self.weight = weight

    # Impression débug pour un arc
    def __repr__(self):
        if self.direction == 'place_to_transition':
            return f"Arc({self.place.name} -> {self.transition.name}, Poids={self.weight})"
        else:
            return f"Arc({self.transition.name} -> {self.place.name}, Poids={self.weight})"


# Représente l'ensemble d'un réseau de Petri
class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.arcs = []
        self.place_counter = 0
        self.transition_counter = 0

    # Pour entièrement reset le réseau
    def wipe(self):
        self.places = {}
        self.transitions = {}
        self.arcs = []
        self.place_counter = 0
        self.transition_counter = 0

    ## ---- Méthodes pour les places ---- ##
    # Rajoute une place
    def add_place(self, name = None):
        if name is None: # nommage automatique si aucun nom est donné
            name = f"P{self.place_counter}"
            self.place_counter += 1
        elif name in self.places: # safety
            raise ValueError("A place with that name already exists.")

        place = Place(name)
        self.places[name] = place
        return place
    
    # Supprime une place
    def delete_place(self, name):
        place = self.places.pop(name, None)
        if not place: # safety
            return
        
        # Supprime aussi les arcs associés
        new_arcs = []
        for arc in self.arcs:
            if arc.place != place:
                new_arcs.append(arc)
        self.arcs = new_arcs

    # Update le nombre de jetons initial d'une place et donc son nombre actuel de jetons
    def set_tokens(self, place_name, amount):
        place = self.places.get(place_name)
        if place:
            place.initial_tokens = amount
            place.tokens = amount

    ## ---- Méthodes pour les transitions ---- ##
    # Rajoute une transition
    def add_transition(self, name=None):
        if name is None: # nommage automatique si aucun nom est donné
            name = f"T{self.transition_counter}"
            self.transition_counter += 1
        elif name in self.transitions: # safety
            raise ValueError("A transition with that name already exists.")

        transition = Transition(name)
        self.transitions[name] = transition
        return transition
    
    # Supprime une transition
    def delete_transition(self, name):
        transition = self.transitions.pop(name, None)
        if not transition: # safety
            return
        
        # Supprime aussi les arcs associés
        new_arcs = []
        for arc in self.arcs:
            if arc.transition != transition:
                new_arcs.append(arc)
        self.arcs = new_arcs

    ## ---- Méthodes pour les arcs ---- ##
    # Rajoute un arc, si possible
    def add_arc(self, a_name, b_name, weight=1):
        # On test quel nom refere a quoi
        a_is_place = a_name in self.places
        a_is_transition = a_name in self.transitions
        b_is_place = b_name in self.places
        b_is_transition = b_name in self.transitions

        # on vérifie que l'arc relie bien une place et une transition et on determine la direction
        if a_is_place and b_is_transition:
            direction = "place_to_transition"
            place = self.places[a_name]
            transition = self.transitions[b_name]
        elif a_is_transition and b_is_place:
            direction = "transition_to_place"
            place = self.places[b_name]
            transition = self.transitions[a_name]
        else: # safety
            raise ValueError("An arc must connect a place and a transition.")

        # on vérifie que l'arc n'existe pas déjà
        for arc in self.arcs:
            if arc.place == place and arc.transition == transition and arc.direction == direction:
                raise ValueError("This arc already exists.")

        # on créé l'arc
        arc = Arc(place, transition, direction, weight)
        self.arcs.append(arc)
        return arc
    
    # Supprime un arc
    def delete_arc(self, place_name, transition_name, direction):
        place = self.places.get(place_name)
        transition = self.transitions.get(transition_name)
        if not place or not transition: # safety
            return
        
        # Recrée la liste des arcs sans celui à supprimer
        new_arcs = []
        for arc in self.arcs:
            if not (arc.place == place and arc.transition == transition and arc.direction == direction):
                new_arcs.append(arc)
        self.arcs = new_arcs

    # Modifie le poids d'un arc
    def modify_arc_weight(self, place_name, transition_name, direction, new_weight):
        place = self.places.get(place_name)
        transition = self.transitions.get(transition_name)
        if not place or not transition: # safety
            return
        
        for arc in self.arcs: # cherche l'arc à modifier
            if arc.place == place and arc.transition == transition and arc.direction == direction:
                arc.weight = new_weight
                print('success' + str(arc)) # debug tbr
                return

    # Donne les arcs entrants
    def get_arcs_entrants(self, transition):
        arcs_entrants = []
        for arc in self.arcs:
            if arc.transition == transition and arc.direction == 'place_to_transition':
                arcs_entrants.append(arc)
        return arcs_entrants

    # Donne les arcs sortants
    def get_arcs_sortants(self, transition):
        arcs_sortants = []
        for arc in self.arcs:
            if arc.transition == transition and arc.direction == 'transition_to_place':
                arcs_sortants.append(arc)
        return arcs_sortants

    # Retourne la liste des transitions tirables
    def get_enabled(self):
        enabled = []
        for transition in self.transitions.values():
            arcs_entrants = self.get_arcs_entrants(transition)
            if transition.is_enabled(arcs_entrants):
                enabled.append(transition)
        return enabled
    
    # Debug - affiche le marquage actuel du réseau
    def display_marking(self):
        print("\n--- Marquage Actuel ---")
        for place in self.places.values():
            print(place)
        print("-----------------------\n")
