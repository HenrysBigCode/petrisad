# logic/simulation.py TO BE TESTED and modified

from logic.petri_net import PetriNet
from logic.analysis import is_deadlocked

class Simulation:
    # Créé un objet qui simule l'exécution d'un réseau de Petri
    def __init__(self, petri_net: PetriNet):
        self.net = petri_net
        self.step_count = 0

    def fire_step(self): #???????????
        enabled = self.net.get_enabled()

        if not enabled:
            return False   # deadlock

        t = enabled[0]     # your simple rule (first enabled)
        inc = self.net.get_arcs_entrants(t)
        out = self.net.get_arcs_sortants(t)

        fired = t.fire(inc, out)
        if fired:
            self.step_count += 1
        return fired

    def run(self, max_steps=10):
        for _ in range(max_steps):
            if not self.fire_step():
                break

    def reset(self):
        for place in self.net.places.values():
            place.tokens = place.initial_tokens
        self.step_count = 0