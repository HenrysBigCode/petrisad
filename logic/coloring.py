# logic/coloring.py

def get_graph_coloring(net):
    """
    Analyse les types (Color Sets) définis dans le réseau.
    Retourne un dictionnaire {nom_sommet: type_donnée}
    """
    node_types = {}
    
    # On récupère les places et on leur assigne un Color Set (Σ)
    for p in net.places:
        name = p.name if hasattr(p, 'name') else str(p)
        # On simule ou récupère le type de donnée de la place
        node_types[name] = getattr(p, 'color_set', 'Integer')

    # Les transitions sont marquées comme ayant des expressions de Garde (G)
    for t in net.transitions:
        name = t.name if hasattr(t, 'name') else str(t)
        node_types[name] = "Guard"
        
    return node_types