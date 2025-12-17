# gui/items.py
import math
from PyQt5.QtWidgets import (QGraphicsLineItem, QGraphicsEllipseItem,
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem)
from PyQt5.QtGui import QPen, QBrush, QColor, QPolygonF, QFont, QPainter
from PyQt5.QtCore import Qt, QLineF, QPointF

from logic.petri_net import Arc

# --- Constantes globales ---
PLACE_RADIUS = 30
TRANSITION_WIDTH = 60
TRANSITION_HEIGHT = 20
ARROW_SIZE = 15
ARROW_ANGLE_DEGREES = 25
ARC_WEIGHT_TEXT_OFFSET = 15 # Augmenté pour être bien sous l'arc
NODE_LABEL_OFFSET_Y = -45 

class ArcItem(QGraphicsLineItem):
    def __init__(self, start_item, end_item, weight=1, parent=None, arc: Arc=None):
        super().__init__(parent)
        self.start_item = start_item
        self.end_item = end_item
        self.weight = weight
        self.backend_arc = arc 

        self.setPen(QPen(Qt.black, 2))
        self.setZValue(-1) 
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.font = QFont("Futura", 12)
        self.font.setBold(True)
        self.update_position()

    def set_weight(self, value):
        self.weight = value
        self.update()

    def boundingRect(self):
        rect = super().boundingRect()
        adjust = max(ARROW_SIZE, ARC_WEIGHT_TEXT_OFFSET) + 10
        return rect.adjusted(-adjust, -adjust, adjust, adjust)

    def update_position(self):
        if not self.start_item or not self.end_item:
            return
        start_center = self.start_item.center_point()
        end_center = self.end_item.center_point()
        self.prepareGeometryChange()
        self.setLine(start_center.x(), start_center.y(), end_center.x(), end_center.y())

    # gui/items.py

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen())
        painter.setFont(self.font)

        line = self.line()
        p1 = line.p1()
        p2 = line.p2()

        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = math.sqrt(dx**2 + dy**2)

        if length == 0: return

        # --- CALCUL DU POINT D'ARRÊT (INTERSECTION BORD) ---
        if isinstance(self.end_item, TransitionItem):
            # Pour une transition (Rectangle), on calcule l'intersection avec les bords
            rect = self.end_item.rect()
            w = rect.width() / 2
            h = rect.height() / 2
            
            # Calcul du ratio basé sur l'angle pour toucher le bord du rectangle
            if abs(dx) * h > abs(dy) * w:
                # Touche un bord vertical (gauche ou droit)
                ratio = w / abs(dx) if dx != 0 else 0
            else:
                # Touche un bord horizontal (haut ou bas)
                ratio = h / abs(dy) if dy != 0 else 0
            
            p2_shortened = QPointF(p2.x() - dx * ratio, p2.y() - dy * ratio)
        else:
            # Pour une Place (Cercle), on utilise le rayon classique
            end_node_radius = PLACE_RADIUS
            ratio = end_node_radius / length
            p2_shortened = QPointF(p2.x() - dx * ratio, p2.y() - dy * ratio)

        # Dessin de la ligne
        dx_s = p2_shortened.x() - p1.x()
        dy_s = p2_shortened.y() - p1.y()
        painter.drawLine(QLineF(p1, p2_shortened))

        # --- DESSIN DE LA FLÈCHE ---
        angle = math.atan2(dy_s, dx_s)
        p_arrow1 = QPointF(
            p2_shortened.x() - ARROW_SIZE * math.cos(angle - math.radians(ARROW_ANGLE_DEGREES)),
            p2_shortened.y() - ARROW_SIZE * math.sin(angle - math.radians(ARROW_ANGLE_DEGREES))
        )
        p_arrow2 = QPointF(
            p2_shortened.x() - ARROW_SIZE * math.cos(angle + math.radians(ARROW_ANGLE_DEGREES)),
            p2_shortened.y() - ARROW_SIZE * math.sin(angle + math.radians(ARROW_ANGLE_DEGREES))
        )
        
        painter.setBrush(QBrush(Qt.black))
        painter.drawPolygon(QPolygonF([p2_shortened, p_arrow1, p_arrow2]))

        # --- POIDS (SOUS L'ARC) ---
        if self.weight > 1:
            mid_x = (p1.x() + p2_shortened.x()) / 2
            mid_y = (p1.y() + p2_shortened.y()) / 2
            dist = ARC_WEIGHT_TEXT_OFFSET
            perp_x = dy_s / length * dist 
            perp_y = -dx_s / length * dist
            painter.drawText(QPointF(mid_x + perp_x - 5, mid_y + perp_y + 5), str(self.weight))

class PlaceItem(QGraphicsEllipseItem):
    def __init__(self, x, y, name=None, radius=PLACE_RADIUS):
        super().__init__(-radius, -radius, 2*radius, 2*radius)
        self.setPen(QPen(QColor("#EF476F"), 2))
        self.setBrush(QBrush(QColor("#FFD166")))
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.name = name if name else "P"
        self.tokens = 0
        self.arcs = []
        self.token_items = []

        self.text_token_fallback = QGraphicsTextItem("", parent=self)
        self.text_token_fallback.setDefaultTextColor(Qt.black)

        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(-self.label.boundingRect().width()/2, -55)
        self.draw_tokens()

    def add_arc(self, arc): self.arcs.append(arc)
    def remove_arc(self, arc): 
        if arc in self.arcs: self.arcs.remove(arc)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for arc in self.arcs: arc.update_position()
        return super().itemChange(change, value)

    def set_tokens(self, v):
        self.tokens = v
        self.draw_tokens()

    def draw_tokens(self):
        # Nettoyage
        for item in self.token_items:
            if item.scene(): self.scene().removeItem(item)
        self.token_items.clear()
        self.text_token_fallback.setPlainText("")

        if 0 < self.tokens <= 5:
            r, off = 5, 12
            positions = {
                1: [(0, 0)],
                2: [(-off, 0), (off, 0)],
                3: [(0, -off), (-off, off), (off, off)],
                4: [(-off, -off), (off, -off), (-off, off), (off, off)],
                5: [(-off, -off), (off, -off), (0,0), (-off, off), (off, off)]
            }[self.tokens]

            for (px,py) in positions:
                dot = QGraphicsEllipseItem(-r, -r, r*2, r*2, parent=self)
                dot.setBrush(QBrush(QColor("#26547C")))
                dot.setPen(QPen(Qt.black))
                dot.setPos(px, py)
                self.token_items.append(dot)

        elif self.tokens > 5:
            # Texte agrandi (Taille 18) quand > 5
            font = QFont("Arial", 18)
            font.setBold(True)
            self.text_token_fallback.setFont(font)
            self.text_token_fallback.setPlainText(str(self.tokens))
            
            bw = self.text_token_fallback.boundingRect().width()
            bh = self.text_token_fallback.boundingRect().height()
            self.text_token_fallback.setPos(-bw/2, -bh/2)

    def center_point(self):
        return self.mapToScene(self.rect().center())


class TransitionItem(QGraphicsRectItem):
    def __init__(self, x, y, name=None, w=TRANSITION_WIDTH, h=TRANSITION_HEIGHT):
        super().__init__(-w/2, -h/2, w, h)
        self.setBrush(QBrush(QColor("#06D6A0")))
        self.setPen(QPen(QColor("#06D6A0"), 2))
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.name = name if name else "T"
        self.arcs = []

        self.label = QGraphicsTextItem(self.name, parent=self)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setPos(-self.label.boundingRect().width()/2, -40)
        
    def add_arc(self, arc): self.arcs.append(arc)
    def remove_arc(self, arc):
        if arc in self.arcs: self.arcs.remove(arc)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for arc in self.arcs: arc.update_position()
        return super().itemChange(change, value)

    def center_point(self):
        return self.mapToScene(self.boundingRect().center())