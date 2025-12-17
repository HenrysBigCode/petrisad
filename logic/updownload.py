# logic/updownload.py
# Module pour l'importation et l'exportation des réseaux de Petri

import json
from logic.petri_net import PetriNet
from gui.items import PlaceItem, TransitionItem, ArcItem
        
        
def save_petri_net(filename, scene, net: PetriNet):
    data = {
        "places": [],
        "transitions": [],
        "arcs": []
    }

    for item in scene.items():
        if isinstance(item, PlaceItem):
            pos = item.scenePos()
            data["places"].append({
                "name": item.name,
                "initial_tokens": net.places.get(item.name).initial_tokens,
                "x": pos.x(),
                "y": pos.y()
            })

        elif isinstance(item, TransitionItem):
            pos = item.scenePos()
            data["transitions"].append({
                "name": item.name,
                "x": pos.x(),
                "y": pos.y()
            })

        elif isinstance(item, ArcItem):
            data["arcs"].append({
                "place": item.backend_arc.place.name,
                "transition": item.backend_arc.transition.name,
                "direction": item.backend_arc.direction,
                "weight": item.backend_arc.weight
            })

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# def import_petri_net_from_json(filename: str) -> PetriNet:
