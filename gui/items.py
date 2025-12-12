# gui/items.py IN CONSTRUCTION

from PyQt5.QtWidgets import (QGraphicsLineItem, QGraphicsEllipseItem,
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem)
from PyQt5.QtGui import QPen, QBrush, QColor
from PyQt5.QtCore import Qt

# Classes graphiques pour les éléments du réseau de Petri

class ArcItem(QGraphicsLineItem):
    # Représente un arc graphique entre une place et une transition (ou l'inverse) MANQUE UNE FLÈCHE?
    def __init__(self, start_item, end_item, weight=1):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.weight = weight

        self.setPen(QPen(QColor("#FFD166"), 2))
        self.setZValue(-1)

        self.weight_label = QGraphicsTextItem(str(weight))
        self.weight_label.setDefaultTextColor(Qt.black)
        self.weight_label.setParentItem(self)
        self.update_positions()

    # Met à jour la position de l'arc en fonction des positions des éléments connectés
    def update_positions(self):
        if not self.start_item.scene() or not self.end_item.scene():
            return
        start_rect = self.start_item.sceneBoundingRect()
        end_rect = self.end_item.sceneBoundingRect()
        s_center = start_rect.center()
        e_center = end_rect.center()
        self.setLine(s_center.x(), s_center.y(), e_center.x(), e_center.y())
        mx = (s_center.x() + e_center.x()) / 2
        my = (s_center.y() + e_center.y()) / 2
        self.weight_label.setPos(mx, my)

    # Met à jour le poids et redessine
    def set_weight(self, value):
        self.weight = value
        self.weight_label.setPlainText(str(value))


class PlaceItem(QGraphicsEllipseItem):
    counter = 1 ## could be 0 ??

    # Représente une place graphique avec des jetons affichés
    def __init__(self, x, y, name=None, radius=30):
        super().__init__(-radius, -radius, 2*radius, 2*radius)
        self.setBrush(QBrush(QColor("#FFFFFF")))
        self.setPen(QPen(QColor("#EF476F"), 2))
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        # Donne un nom unique si aucun n'est fourni TO BE CHANGED TO CHECK FOR DOUBLES? UNLESS ITS ONLY INTERNAL?
        if name is None:
            self.name = f"P{PlaceItem.counter}"
            PlaceItem.counter += 1
        else:
            self.name = name

        self.tokens = 0
        self.arcs = []

        self.token_items = [] # Liste pour stocker les objets graphiques des jetons (les points noirs)
        
        self.text_token_fallback = QGraphicsTextItem("", parent=self) # Label textuel (utilisé uniquement si trop de jetons)
        self.text_token_fallback.setDefaultTextColor(Qt.black)

        self.label = QGraphicsTextItem(self.name, parent=self) # Label du Nom (P1, P2...)
        self.label.setPos(-10, -45) # Un peu plus haut pour ne pas gêner
        
        self.draw_tokens() # On dessine l'état initial (0 jeton) usefull ?

    # Gestion des arcs connectés
    def add_arc(self, arc):
        self.arcs.append(arc)

    def remove_arc(self, arc):
        if arc in self.arcs:
            self.arcs.remove(arc)

    # bouge les arcs si la place bouge -> appelé automatiquement par Qt
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for arc in list(self.arcs):
                arc.update_positions()
        return super().itemChange(change, value)

    # Met à jour le nombre de jetons et redessine
    def set_tokens(self, v):
        self.tokens = v
        self.draw_tokens()

    # Dessine les jetons en fonction du nombre actuel de jetons
    def draw_tokens(self):
        # 1. On nettoie tout (on enlève les anciens points et le texte)
        for item in self.token_items:
            if item.scene():
                self.scene().removeItem(item)
            else:
                item.setParentItem(None)
        self.token_items.clear()
        self.text_token_fallback.setPlainText("")

        # 2. Configuration des points
        r_token = 5 # Rayon du point noir
        offset = 12 # Écartement par rapport au centre

        positions = [] # Positions prédéfinies pour être joli (coordonnées relatives au centre 0,0)
        
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

        # 3. Dessin des jetons
        if 0 < self.tokens <= 5:
            for (px,py) in positions: # On dessine les ronds noirs
                dot = QGraphicsEllipseItem(-r_token, -r_token, r_token*2, r_token*2)
                dot.setBrush(QBrush(QColor("#26547C")))
                dot.setPen(QPen(Qt.black))
                dot.setParentItem(self) # On l'attache à la Place
                dot.setPos(px, py)
                self.token_items.append(dot)

        elif self.tokens > 5:
            # Si trop de jetons, on affiche le chiffre au centre
            self.text_token_fallback.setPlainText(str(self.tokens))
            # On centre le texte de manière barbare)
            font_width = self.text_token_fallback.boundingRect().width()
            font_height = self.text_token_fallback.boundingRect().height()
            self.text_token_fallback.setPos(-font_width/2, -font_height/2)


class TransitionItem(QGraphicsRectItem):
    counter = 1 ## could be 0 ??

    # Représente une transition graphique
    def __init__(self, x, y, name=None, w=60, h=20):
        super().__init__(-w/2, -h/2, w, h)
        self.setBrush(QBrush(QColor("#06D6A0")))
        self.setPen(QPen(QColor("#06D6A0"), 2))
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        # Donne un nom unique si aucun n'est fourni TO BE CHANGED TO CHECK FOR DOUBLES? UNLESS ITS ONLY INTERNAL?
        if name is None:
            self.name = f"T{TransitionItem.counter}"
            TransitionItem.counter += 1
        else:
            self.name = name

        self.arcs = []
        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setPos(-10, -40)

    # Gestion des arcs connectés
    def add_arc(self, arc):
        self.arcs.append(arc)

    def remove_arc(self, arc):
        if arc in self.arcs:
            self.arcs.remove(arc)

    # bouge les arcs si la transition bouge -> appelé automatiquement par Qt
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for arc in list(self.arcs):
                arc.update_positions()
        return super().itemChange(change, value)