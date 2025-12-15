# logic/updownload.py
# Module pour l'importation et l'exportation des réseaux de Petri

import json
from logic.petri_net import PetriNet, Place, Transition, Arc

def export_petri_net_to_json(net: PetriNet, filename: str):
    data = {
        "places": [
            {"name": place.name, "initial_tokens": place.initial_tokens}
            for place in net.places.values()
        ],
        "transitions": [
            {"name": transition.name}
            for transition in net.transitions.values()
        ],
        "arcs": [
            {
                "place": arc.place.name,
                "transition": arc.transition.name,
                "direction": arc.direction,
                "weight": arc.weight
            }
            for arc in net.arcs
        ]
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# def import_petri_net_from_json(filename: str) -> PetriNet:
