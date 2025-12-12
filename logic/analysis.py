# logic/analisis.py TO BE TESTED and modified

from logic.petri_net import PetriNet

# return True si le réseau est en deadlock
def is_deadlocked(net: PetriNet):
    return len(net.get_enabled()) == 0

"""
def checkLoop(self):
        # Placeholder for loop detection logic
        pass

def checkVivacity(self):
    # Placeholder for vivacity detection logic
    pass

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