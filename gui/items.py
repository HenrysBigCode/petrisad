# gui/items.py - Version CORRIGÉE

import math
from PyQt5.QtWidgets import (QGraphicsLineItem, QGraphicsEllipseItem,
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem)
from PyQt5.QtGui import QPen, QBrush, QColor, QPolygonF, QFont
from PyQt5.QtCore import Qt, QLineF, QPointF # pyqtSignal n'est pas utilisé dans cette version, donc retiré.

# --- Constantes globales pour les styles (optionnel, mais bonne pratique) ---
PLACE_RADIUS = 30
TRANSITION_WIDTH = 60
TRANSITION_HEIGHT = 20
ARROW_SIZE = 15
ARROW_ANGLE_DEGREES = 25
ARC_WEIGHT_TEXT_OFFSET = 10
NODE_LABEL_OFFSET_Y = -45 


# on crée les classes graphiques pour les éléments du réseau de Petri

class ArcItem(QGraphicsLineItem):
    
    def __init__(self, start_item, end_item, weight=1, parent=None):
        super().__init__(parent)
        self.start_item = start_item
        self.end_item = end_item
        self.weight = weight

        self.setPen(QPen(Qt.black, 2))
        self.setZValue(-1) # Les arcs sont placés derrière les places et transitions

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) 

        # Police pour le texte du poids
        self.font = QFont()
        self.font.setPointSize(12) 

        # Appel initial pour positionner l'arc.
        self.update_position()

        
    def set_weight(self, value):
        self.weight = value
        self.update() # on force Qt à redessiner l'arc pour afficher le nouveau chiffre

    
    def boundingRect(self):
        # boundingRect est utilisé par Qt pour savoir quelle zone doit être redessinée.
        rect = super().boundingRect()
        # On l'agrandit pour inclure la flèche et le texte du poids.
        
        adjust = max(ARROW_SIZE, ARC_WEIGHT_TEXT_OFFSET) + 5 
        return rect.adjusted(-adjust, -adjust, adjust, adjust)

    def update_position(self):
        # update_position met à jour la position de l'arc en fonction des éléments connectés.
        #Elle est appelée lorsque les éléments de début ou de fin bougent.
       
        if not self.start_item or not self.end_item:
            return

        # on vérifie que les éléménets ont la méthode center_point()
        if not hasattr(self.start_item, 'center_point') or not hasattr(self.end_item, 'center_point'):
            print("Erreur : l'élément de début ou de fin ne possède pas la méthode center_point().")
            return

        start_center = self.start_item.center_point()
        end_center = self.end_item.center_point()

    
        
        self.prepareGeometryChange()
        self.setLine(start_center.x(), start_center.y(), end_center.x(), end_center.y())


    
    def paint(self, painter, option, widget=None):
        
        # paint permet de dessiner l'arc avec une flèche et le poids.

        painter.setRenderHint(painter.Antialiasing) 
        painter.setPen(self.pen())
        painter.setFont(self.font)

        line = self.line()
        p1 = line.p1() 
        p2 = line.p2() 

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = math.sqrt(dx**2 + dy**2)

        
        if length == 0:
            return

       # Tout ce qui suit est fait pour qu'on voit bien la flèche à l'extrémité de l'arc,
         # sans qu'elle rentre dans le noeud de fin (place ou transition).
        end_node_radius = PLACE_RADIUS # Rayon par défaut pour une Place

        # Si l'élément de fin est une Transition, son "rayon" effectif est la moitié de sa hauteur pour l'arc
        if isinstance(self.end_item, TransitionItem):
            end_node_radius = TRANSITION_HEIGHT / 2

        if length > end_node_radius:
            # Calcul du point final de la ligne après raccourcissement
            ratio = end_node_radius / length
            p2_shortened = QPointF(p2.x() - dx * ratio, p2.y() - dy * ratio)
        else:
            # Si l'arc est plus court que le rayon, on ne le dessine pas
            p2_shortened = p2

       
        dx_shortened = p2_shortened.x() - p1.x()
        dy_shortened = p2_shortened.y() - p1.y()
        length_shortened = math.sqrt(dx_shortened**2 + dy_shortened**2)

        # Si la ligne raccourcie est maintenant de longueur nulle, ne pas dessiner
        if length_shortened == 0:
            return

        # on dessine la ligne principale de l'arc
        painter.drawLine(QLineF(p1, p2_shortened))

        # on dessine la flèche à l'extrémité
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

        # on dessine le poids de l'arc
        if self.weight > 1:
            # Point milieu de la ligne réellement dessinée (entre p1 et p2_shortened)
            mid_x = (p1.x() + p2_shortened.x()) / 2
            mid_y = (p1.y() + p2_shortened.y()) / 2

            
            perp_x = -dy_shortened / length_shortened * ARC_WEIGHT_TEXT_OFFSET
            perp_y = dx_shortened / length_shortened * ARC_WEIGHT_TEXT_OFFSET

           
            text_pos = QPointF(mid_x + perp_x, mid_y + perp_y)
            painter.drawText(text_pos, str(self.weight))


class PlaceItem(QGraphicsEllipseItem):
    
    # classe pour créer des places graphiques
    counter = 1

    def __init__(self, x, y, name=None, radius=PLACE_RADIUS):
        super().__init__(-radius, -radius, 2*radius, 2*radius) # x, y, w, h pour l'ellipse
        self.setPen(QPen(QColor("#EF476F"), 2))
        self.setBrush(QBrush(QColor("#FFD166"))) 
        self.setPos(x, y) # on positionne le centre de l'ellipse
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) # nécessaire pour le drag & drop

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
        # Ajoute un arc à la liste des arcs connectés.
        self.arcs.append(arc)

    def remove_arc(self, arc):
        # Supprime un arc de la liste des arcs connectés.
        if arc in self.arcs:
            self.arcs.remove(arc)

    def itemChange(self, change, value):
        # appelée par Qt lorsque des propriétés de l'élément changent.
        #met à jour les arcs connectés lorsque la place bouge.
        
        if change == QGraphicsItem.ItemPositionChange:
            # Quand la place bouge, on demande à tous les arcs connectés de se mettre à jour
            for arc in list(self.arcs): 
                arc.update_position() 
        return super().itemChange(change, value)

    def set_tokens(self, v):
        #gère le changement du nombre de jetons dans la place
        self.tokens = v
        self.draw_tokens()

    def draw_tokens(self):
        # dessine les jetons dans la place en fonction du nombre de jetons
        # en premier, on enlève tous les jetons existants
        for item in self.token_items:
            if item.scene():
                self.scene().removeItem(item)
            else:
                item.setParentItem(None) 
        self.token_items.clear()
        self.text_token_fallback.setPlainText("") # Efface le texte de fallback

        # Paramètres pour le dessin des points jetons
        r_token = 5
        offset = 12

        positions = [] 

        # Définition des positions pour 1 à 5 jetons, au delà on utilisera le texte
        if self.tokens == 1:
            positions = [(0, 0)]
        elif self.tokens == 2:
            positions = [(-offset, 0), (offset, 0)]
        elif self.tokens == 3: 
            positions = [(0, -offset), (-offset, offset), (offset, offset)]
        elif self.tokens == 4: 
            positions = [(-offset, -offset), (offset, -offset), (-offset, offset), (offset, offset)]
        elif self.tokens == 5: 
            positions = [(-offset, -offset), (offset, -offset), (0,0), (-offset, offset), (offset, offset)]

        
        if 0 < self.tokens <= 5:
            for (px,py) in positions:
                dot = QGraphicsEllipseItem(-r_token, -r_token, r_token*2, r_token*2)
                dot.setBrush(QBrush(QColor("#26547C"))) # Couleur des jetons
                dot.setPen(QPen(Qt.black))
                dot.setParentItem(self) # Attache le jeton à la place 
                dot.setPos(px, py)
                self.token_items.append(dot)

        elif self.tokens > 5:
            # si + de 5 jetons afficher le chiffre au centre
            self.text_token_fallback.setPlainText(str(self.tokens))
            # centrer le texte
            font_width = self.text_token_fallback.boundingRect().width()
            font_height = self.text_token_fallback.boundingRect().height()
            self.text_token_fallback.setPos(-font_width/2, -font_height/2)

    def center_point(self):
        return self.mapToScene(self.rect().center())


class TransitionItem(QGraphicsRectItem):
    
    counter = 1

    def __init__(self, x, y, name=None, w=TRANSITION_WIDTH, h=TRANSITION_HEIGHT):
        super().__init__(-w/2, -h/2, w, h) 
        self.setBrush(QBrush(QColor("#06D6A0"))) 
        self.setPen(QPen(QColor("#06D6A0"), 2))
        self.setPos(x, y) #centre du rectangle
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges) # Important pour déplacer les arcs

        if name is None:
            self.name = f"T{TransitionItem.counter}"
            TransitionItem.counter += 1
        else:
            self.name = name

        self.arcs = [] #liste des arcs connectés à la transition

        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setPos(-self.label.boundingRect().width()/2, NODE_LABEL_OFFSET_Y) 

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
            #transition bouge donc tous les arcs connectés de se mettre à jour
            for arc in list(self.arcs):
                arc.update_position()
        return super().itemChange(change, value)

    def center_point(self):
        """
        Retourne le point central de la transition en coordonnées de scène.
        Nécessaire pour le calcul de la position des arcs.
        """
        return self.mapToScene(self.boundingRect().center())
    
    
