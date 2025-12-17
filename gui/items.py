# gui/items.py - Version CORRIGÉE

import math
from PyQt5.QtWidgets import (QGraphicsLineItem, QGraphicsEllipseItem,
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem)
from PyQt5.QtGui import QPen, QBrush, QColor, QPolygonF, QFont
from PyQt5.QtCore import Qt, QLineF, QPointF # pyqtSignal n'est pas utilisé dans cette version, donc retiré.

from logic.petri_net import Arc

# --- Constantes globales pour les styles (optionnel, mais bonne pratique) ---
PLACE_RADIUS = 30
TRANSITION_WIDTH = 60
TRANSITION_HEIGHT = 20
ARROW_SIZE = 15
ARROW_ANGLE_DEGREES = 25
ARC_WEIGHT_TEXT_OFFSET = 10
NODE_LABEL_OFFSET_Y = -45 # Offset vertical pour les labels de nœuds


# --- Classes graphiques pour les éléments du réseau de Petri ---

class ArcItem(QGraphicsLineItem):
    """
    Représente un arc graphique reliant deux éléments (Place ou Transition)
    dans une scène QGraphicsView. Il dessine une ligne, une flèche
    et le poids de l'arc.
    """
    def __init__(self, start_item, end_item, weight=1, parent=None, arc: Arc=None):
        super().__init__(parent)
        self.start_item = start_item
        self.end_item = end_item
        self.weight = weight
        self.backend_arc = arc  # Référence à l'arc backend correspondant

        self.setPen(QPen(Qt.black, 2))
        self.setZValue(-1) # Les arcs sont derrière les Places/Transitions

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) # Pour que itemChange soit appelé si on le déplace (pas direct pour un arc)

        # Assurez-vous que le texte du poids est bien centré et lisible
        self.font = QFont()
        self.font.setPointSize(9) # Taille de police pour le poids de l'arc

        # Appel initial pour positionner l'arc.
        # prepareGeometryChange() est appelé à l'intérieur de update_position().
        self.update_position()

        # REMARQUE : Les connexions de signaux comme 'position_changed'
        # ne sont pas nécessaires ici. L'update est gérée par la méthode
        # 'itemChange' des éléments de début et de fin, qui appelle
        # directement 'self.update_position()'.
    def set_weight(self, value):
        self.weight = value
        self.update() # Important : force Qt à redessiner l'arc pour afficher le nouveau chiffre

    # --- 1. CRUCIAL : Définir la zone de dessin ---
    # Cette méthode est essentielle pour que Qt sache quelle partie de la scène
    # doit être redessinée quand l'élément bouge ou change, et pour la sélection.
    def boundingRect(self):
        # On commence avec la zone de délimitation de la ligne de base.
        rect = super().boundingRect()
        # On l'agrandit pour inclure la flèche et le texte du poids.
        # Sans cet ajustement, la flèche et/ou le texte pourraient être coupés
        # si leur dessin dépasse la ligne elle-même.
        adjust = max(ARROW_SIZE, ARC_WEIGHT_TEXT_OFFSET) + 5 # +5 pour un petit padding
        return rect.adjusted(-adjust, -adjust, adjust, adjust)

    def update_position(self):
        """
        Met à jour la position de l'arc en fonction des positions
        centrales de ses éléments de début et de fin.
        Appelée lorsque les éléments de début ou de fin bougent.
        """
        if not self.start_item or not self.end_item:
            return

        # Vérifie que les éléments ont bien la méthode center_point()
        if not hasattr(self.start_item, 'center_point') or not hasattr(self.end_item, 'center_point'):
            print("Erreur : l'élément de début ou de fin ne possède pas la méthode center_point().")
            return

        start_center = self.start_item.center_point()
        end_center = self.end_item.center_point()

        # Informer Qt que la géométrie de cet élément va changer
        # (important pour la mise à jour du boundingRect et le redessin).
        self.prepareGeometryChange()
        self.setLine(start_center.x(), start_center.y(), end_center.x(), end_center.y())


    # --- 2. DESSIN : Recul + Triangle + Texte ---
    def paint(self, painter, option, widget=None):
        """
        Méthode de dessin de l'arc. Dessine la ligne, la flèche et le poids.
        """
        painter.setRenderHint(painter.Antialiasing) # Pour des lignes plus lisses
        painter.setPen(self.pen())
        painter.setFont(self.font)

        line = self.line()
        p1 = line.p1() # Point de départ réel
        p2 = line.p2() # Point d'arrivée réel

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = math.sqrt(dx**2 + dy**2)

        # Si l'arc est de longueur nulle (points superposés), on ne dessine rien pour éviter les erreurs.
        if length == 0:
            return

        # --- A. On raccourcit la ligne pour s'arrêter au bord de l'élément de fin ---
        # Cette "marge" devrait idéalement être le rayon de l'élément de fin.
        # Pour simplifier, nous utilisons une constante ou le rayon d'une place.
        # Il faudrait idéalement une méthode 'get_radius()' sur PlaceItem/TransitionItem.
        # Pour l'instant, on estime le rayon de fin (ex: PLACE_RADIUS ou TRANSITION_HEIGHT/2)
        end_node_radius = PLACE_RADIUS # Par défaut, on utilise le rayon de la Place

        # Si l'élément de fin est une Transition, son "rayon" effectif est la moitié de sa hauteur pour l'arc
        if isinstance(self.end_item, TransitionItem):
            end_node_radius = TRANSITION_HEIGHT / 2

        if length > end_node_radius:
            # Calcul du point final de la ligne après raccourcissement
            ratio = end_node_radius / length
            p2_shortened = QPointF(p2.x() - dx * ratio, p2.y() - dy * ratio)
        else:
            # Si la ligne est trop courte ou égale au rayon, on la dessine jusqu'à p2
            # ou on ne la raccourcit pas. Pour éviter un arc qui rentre dans le noeud,
            # on peut décider de ne rien dessiner si c'est trop court.
            # Pour cet exemple, nous allons dessiner une ligne très courte mais sans raccourcir.
            p2_shortened = p2

        # Re-calculer dx, dy, length pour la ligne réellement dessinée (jusqu'à p2_shortened)
        dx_shortened = p2_shortened.x() - p1.x()
        dy_shortened = p2_shortened.y() - p1.y()
        length_shortened = math.sqrt(dx_shortened**2 + dy_shortened**2)

        # Si la ligne raccourcie est maintenant de longueur nulle, ne pas dessiner
        if length_shortened == 0:
            return

        # --- B. On dessine la ligne principale de l'arc ---
        painter.drawLine(QLineF(p1, p2_shortened))

        # --- C. On dessine la flèche à l'extrémité de la ligne raccourcie ---
        angle = math.atan2(dy_shortened, dx_shortened) # Angle de la ligne raccourcie

        # Calcul des deux points de base du triangle de la flèche
        p_arrow1 = QPointF(
            p2_shortened.x() - ARROW_SIZE * math.cos(angle - math.radians(ARROW_ANGLE_DEGREES)),
            p2_shortened.y() - ARROW_SIZE * math.sin(angle - math.radians(ARROW_ANGLE_DEGREES))
        )
        p_arrow2 = QPointF(
            p2_shortened.x() - ARROW_SIZE * math.cos(angle + math.radians(ARROW_ANGLE_DEGREES)),
            p2_shortened.y() - ARROW_SIZE * math.sin(angle + math.radians(ARROW_ANGLE_DEGREES))
        )

        # Création et dessin du polygone de la flèche
        arrow_head = QPolygonF([p2_shortened, p_arrow1, p_arrow2])
        painter.setBrush(QBrush(Qt.black)) # Remplissage explicite en noir
        painter.drawPolygon(arrow_head)

        # --- D. Texte du poids de l'arc ---
        if self.weight > 1:
            # Point milieu de la ligne réellement dessinée (entre p1 et p2_shortened)
            mid_x = (p1.x() + p2_shortened.x()) / 2
            mid_y = (p1.y() + p2_shortened.y()) / 2

            # Vecteur perpendiculaire à la ligne pour décaler le texte
            perp_x = -dy_shortened / length_shortened * ARC_WEIGHT_TEXT_OFFSET
            perp_y = dx_shortened / length_shortened * ARC_WEIGHT_TEXT_OFFSET

            # Position finale du texte
            text_pos = QPointF(mid_x + perp_x, mid_y + perp_y)
            painter.drawText(text_pos, str(self.weight))


class PlaceItem(QGraphicsEllipseItem):
    """
    Représente une place graphique dans le réseau de Petri.
    Peut afficher des jetons sous forme de points ou un chiffre.
    """
    counter = 1

    def __init__(self, x, y, name=None, radius=PLACE_RADIUS):
        super().__init__(-radius, -radius, 2*radius, 2*radius) # x, y, w, h pour l'ellipse
        self.setPen(QPen(QColor("#EF476F"), 2))
        self.setBrush(QBrush(QColor("#FFD166"))) # AJOUTÉ : Brush par défaut pour la place
        self.setPos(x, y) # Positionne le centre de l'ellipse
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) # Important pour déplacer les arcs

        if name is None:
            self.name = f"P{PlaceItem.counter}"
            PlaceItem.counter += 1
        else:
            self.name = name

        self.tokens = 0
        self.arcs = [] # Liste des arcs connectés à cette place

        self.token_items = [] # Pour stocker les QGraphicsEllipseItem des jetons
        # Texte de fallback pour plus de 5 jetons
        self.text_token_fallback = QGraphicsTextItem("", parent=self)
        self.text_token_fallback.setDefaultTextColor(Qt.black)
        self.text_token_fallback.setFont(QFont("Arial", 10))


        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setPos(-self.label.boundingRect().width()/2, NODE_LABEL_OFFSET_Y) # Centre le label au-dessus

        self.draw_tokens() # Dessine les jetons initialement

    def add_arc(self, arc):
        """Ajoute un arc à la liste des arcs connectés."""
        self.arcs.append(arc)

    def remove_arc(self, arc):
        """Supprime un arc de la liste des arcs connectés."""
        if arc in self.arcs:
            self.arcs.remove(arc)

    def itemChange(self, change, value):
        """
        Est appelée par Qt lorsque des propriétés de l'élément changent.
        Utilisée ici pour mettre à jour les arcs connectés lorsque la place bouge.
        """
        if change == QGraphicsItem.ItemPositionChange:
            # Quand la place bouge, on demande à tous les arcs connectés de se mettre à jour
            for arc in list(self.arcs): # Utilisez list() pour éviter les problèmes si un arc est supprimé
                arc.update_position() # CORRIGÉ : update_positions() -> update_position()
        return super().itemChange(change, value)

    def set_tokens(self, v):
        """Met à jour le nombre de jetons et redessine l'affichage des jetons."""
        self.tokens = v
        self.draw_tokens()

    def draw_tokens(self):
        """
        Dessine visuellement les jetons (points noirs ou texte) à l'intérieur de la place.
        """
        # 1. Nettoyage : supprimer tous les anciens jetons/texte
        for item in self.token_items:
            if item.scene():
                self.scene().removeItem(item)
            else:
                item.setParentItem(None) # S'il n'est plus dans la scène, juste détacher
        self.token_items.clear()
        self.text_token_fallback.setPlainText("") # Efface le texte de fallback

        # Paramètres pour le dessin des points jetons
        r_token = 5
        offset = 12

        positions = [] # Positions relatives au centre (0,0) pour les jetons

        # Définition des positions pour 1 à 5 jetons
        if self.tokens == 1:
            positions = [(0, 0)]
        elif self.tokens == 2:
            positions = [(-offset, 0), (offset, 0)]
        elif self.tokens == 3: # Triangle
            positions = [(0, -offset), (-offset, offset), (offset, offset)]
        elif self.tokens == 4: # Carré
            positions = [(-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset)]
        elif self.tokens == 5: # Façon Dé 5
            positions = [(-offset, -offset), (offset, -offset), (0,0), (-offset, offset), (offset, offset)]

        # Dessin des jetons si le nombre est entre 1 et 5
        if 0 < self.tokens <= 5:
            for (px,py) in positions:
                dot = QGraphicsEllipseItem(-r_token, -r_token, r_token*2, r_token*2)
                dot.setBrush(QBrush(QColor("#26547C"))) # Couleur des jetons
                dot.setPen(QPen(Qt.black))
                dot.setParentItem(self) # Attache le jeton à la place (coordonnées relatives)
                dot.setPos(px, py)
                self.token_items.append(dot)

        elif self.tokens > 5:
            # Si trop de jetons, afficher le chiffre au centre
            self.text_token_fallback.setPlainText(str(self.tokens))
            # Centrer le texte
            font_width = self.text_token_fallback.boundingRect().width()
            font_height = self.text_token_fallback.boundingRect().height()
            self.text_token_fallback.setPos(-font_width/2, -font_height/2)

    def center_point(self):
        """
        Retourne le point central de la place en coordonnées de scène.
        Nécessaire pour le calcul de la position des arcs.
        """
        return self.mapToScene(self.rect().center())


class TransitionItem(QGraphicsRectItem):
    """
    Représente une transition graphique dans le réseau de Petri.
    """
    counter = 1

    def __init__(self, x, y, name=None, w=TRANSITION_WIDTH, h=TRANSITION_HEIGHT):
        super().__init__(-w/2, -h/2, w, h) # x, y, w, h pour le rectangle (centré)
        self.setBrush(QBrush(QColor("#06D6A0"))) # Couleur de la transition
        self.setPen(QPen(QColor("#06D6A0"), 2))
        self.setPos(x, y) # Positionne le centre du rectangle
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) # Important pour déplacer les arcs

        if name is None:
            self.name = f"T{TransitionItem.counter}"
            TransitionItem.counter += 1
        else:
            self.name = name

        self.arcs = [] # Liste des arcs connectés à cette transition

        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setPos(-self.label.boundingRect().width()/2, NODE_LABEL_OFFSET_Y) # Centre le label au-dessus

    def add_arc(self, arc):
        """Ajoute un arc à la liste des arcs connectés."""
        self.arcs.append(arc)

    def remove_arc(self, arc):
        """Supprime un arc de la liste des arcs connectés."""
        if arc in self.arcs:
            self.arcs.remove(arc)

    def itemChange(self, change, value):
        """
        Est appelée par Qt lorsque des propriétés de l'élément changent.
        Utilisée ici pour mettre à jour les arcs connectés lorsque la transition bouge.
        """
        if change == QGraphicsItem.ItemPositionChange:
            # Quand la transition bouge, on demande à tous les arcs connectés de se mettre à jour
            for arc in list(self.arcs):
                arc.update_position() # CORRIGÉ : update_positions() -> update_position()
        return super().itemChange(change, value)

    def center_point(self):
        """
        Retourne le point central de la transition en coordonnées de scène.
        Nécessaire pour le calcul de la position des arcs.
        """
        return self.mapToScene(self.boundingRect().center())
