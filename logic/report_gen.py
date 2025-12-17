import os
import matplotlib.pyplot as plt
import networkx as nx
from fpdf import FPDF
from logic.analysis import StateSpaceVisualizer, build_state_space, checkVivacity, checkLoop

def generate_pdf_report(net, filename):
    viz = StateSpaceVisualizer()
    build_state_space(net, viz)
    
    vivacity_lvl = checkVivacity(net)
    has_loop = checkLoop(net)
    is_initially_blocked = len(net.get_enabled()) == 0
    num_states = len(viz.graph.nodes)

    img_path = "temp_ss.png"
    plt.figure(figsize=(12, 10)) 
    
    # --- CHANGEMENT POUR LA LISIBILITÉ EN ARBRE ---
    try:
        # Tente d'utiliser Graphviz pour un vrai rendu en arbre (nécessite pygraphviz ou pydot)
        from networkx.drawing.nx_pydot import graphviz_layout
        pos = graphviz_layout(viz.graph, prog='dot')
    except ImportError:
        # Solution de repli : un layout qui simule une hiérarchie par couches (Shell Layout)
        # On peut aussi utiliser multipartite_layout si on définit des couches
        pos = nx.shell_layout(viz.graph)
    
    colors = [data['color'] for node, data in viz.graph.nodes(data=True)]
    labels = nx.get_node_attributes(viz.graph, 'label')
    
    # Dessin des arêtes avec des courbes pour éviter les superpositions sur les noms
    nx.draw(viz.graph, pos, with_labels=True, labels=labels, 
            node_color=colors, node_size=3500, font_size=7, 
            edge_color='gray', arrowsize=20, connectionstyle='arc3, rad=0.1')
    
    plt.title("Arbre d'Accessibilité (Espace d'États)")
    plt.savefig(img_path, bbox_inches='tight')
    plt.close()

    # --- GÉNÉRATION PDF (2 PAGES) ---
    pdf = FPDF()
    
    # PAGE 1 : GRAPHE
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(7, 59, 76)
    pdf.cell(200, 20, txt="Rapport d'Analyse Réseau de Petri", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(239, 71, 111)
    pdf.cell(200, 10, txt="1. Arbre d'Accessibilité", ln=True)
    pdf.image(img_path, x=10, y=55, w=190)

    # PAGE 2 : ANALYSE
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(239, 71, 111)
    pdf.cell(200, 10, txt="2. Analyse des Propriétés", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    
    status_v = {
        0: "Partiellement Mort (Des impasses existent)", 
        1: "Vivant Faible (Certaines transitions sont mortes)", 
        2: "Vivant Parfait (Aucun blocage possible)"
    }
    
    pdf.cell(200, 10, txt=f" - Vivacité globale : {status_v[vivacity_lvl]}", ln=True)
    pdf.cell(200, 10, txt=f" - État au lancement : {'BLOQUÉ' if is_initially_blocked else 'OPÉRATIONNEL'}", ln=True)
    pdf.cell(200, 10, txt=f" - Bornitude : Borné ({num_states} états distincts trouvés)", ln=True)
    pdf.cell(200, 10, txt=f" - Cycles structurels : {'Présents' if has_loop else 'Aucun cycle détecté'}", ln=True)

    pdf.output(filename)
    if os.path.exists(img_path):
        os.remove(img_path)