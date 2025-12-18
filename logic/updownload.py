# logic/updownload.py
# Module pour l'importation et l'exportation des réseaux de Petri

import json
from logic.petri_net import PetriNet
from gui.items import PlaceItem, TransitionItem, ArcItem

# transforme un réseau de Petri et une scène en json de sauvegarde
def save_petri_net(filename, scene, net: PetriNet):
    # Prépare les données à sauvegarder
    data = {
        "places": [],
        "transitions": [],
        "arcs": []
    }

    # On construit à partir des items de la scène et du backend
    for item in scene.items():
        # --- Places --- #
        if isinstance(item, PlaceItem):
            pos = item.scenePos()
            data["places"].append({
                "name": item.name,
                "initial_tokens": net.places.get(item.name).initial_tokens,
                "x": pos.x(),
                "y": pos.y()
            })
        # --- Transitions --- #
        elif isinstance(item, TransitionItem):
            pos = item.scenePos()
            data["transitions"].append({
                "name": item.name,
                "x": pos.x(),
                "y": pos.y()
            })
        # --- Arcs --- #
        elif isinstance(item, ArcItem):
            data["arcs"].append({
                "place": item.backend_arc.place.name,
                "transition": item.backend_arc.transition.name,
                "direction": item.backend_arc.direction,
                "weight": item.backend_arc.weight
            })

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


# transforme un json de sauvegarde en réseau de Petri pour la scène et le backend
def load_petri_net(filename, scene, petri_net):
    try:
        with open(filename) as f:
            data = json.load(f) # on lit le fichier
    except Exception as e: # safety
        return False, f"Cannot read file:\n{e}"

    # safety - vérifie que les clés principales existent
    for key in ("places", "transitions", "arcs"):
        if key not in data:
            return False, f"Invalid file: missing '{key}'"

    place_items = {}
    transition_items = {}

    # --- Places --- #
    for p in data["places"]:
        try:
            backend_place = petri_net.add_place(name=p["name"])
            petri_net.place_counter += 1
            backend_place.initial_tokens = p["initial_tokens"]
            backend_place.tokens = p["initial_tokens"]
            
            item = PlaceItem(p["x"], p["y"], name=backend_place.name)
            item.tokens = backend_place.initial_tokens
            item.draw_tokens()
            scene.addItem(item)
            place_items[backend_place.name] = item
        except KeyError: # safety
            return False, "Invalid place entry in file"

    # --- Transitions --- #
    for t in data["transitions"]:
        try:
            backend_t = petri_net.add_transition(name=t["name"])
            petri_net.transition_counter += 1
            
            item = TransitionItem(t["x"], t["y"], name=backend_t.name)
            scene.addItem(item)
            transition_items[backend_t.name] = item
        except KeyError: # safety
            return False, "Invalid transition entry in file"

    # --- Arcs --- #
    for a in data["arcs"]:
        try:
            p_name = a["place"]
            t_name = a["transition"]

            if p_name not in place_items or t_name not in transition_items:
                continue  # safety

            if a["direction"] == "place_to_transition": # on determine les items gui à relier
                start_item = place_items[p_name]
                end_item = transition_items[t_name]
            else:
                start_item = transition_items[t_name]
                end_item = place_items[p_name]

            try:
                arc_backend = petri_net.add_arc(start_item.name, end_item.name, weight=a["weight"]) # on crée l'arc dans le backend
            except Exception as e: # safety
                return False, "Arc creation failed on backend"

            item = ArcItem(start_item, end_item, weight=a["weight"], arc=arc_backend) # on crée l'arc dans la scène
            scene.addItem(item)
            start_item.add_arc(item)
            end_item.add_arc(item)

        except KeyError: # safety
            continue

    return True, "OK", place_items, transition_items # on retourne la liste des items créés et des indications de succès