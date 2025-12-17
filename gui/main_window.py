# gui/main_window.py
import math
from PyQt5.QtWidgets import (QWidget, QFrame, QPushButton,
                             QFormLayout, QLabel, QSpinBox, QHBoxLayout, QVBoxLayout)
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QPen
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog

from gui.items import PlaceItem, TransitionItem, ArcItem
from logic.updownload import save_petri_net

class Mode:
    #modes différents
    SELECT = 0
    ADD_PLACE = 1
    ADD_TRANSITION = 2
    ADD_ARC = 3


class PetriGraphicsView(QGraphicsView):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setSceneRect(0, 0, 2000, 2000)
        self.setRenderHints(QPainter.Antialiasing)
        self.mode = None
        self.temp_arc_start = None

        # --- AJOUT DU BOUTON EFFACER TOUT ---
        self.btn_clear_all = QPushButton("Effacer tout", self)
        # On lui donne un style un peu différent pour qu'il se distingue sur fond blanc
        self.btn_clear_all.setStyleSheet("""
            QPushButton {
                background-color: #EF476F; 
                color: white; 
                border-radius: 5px; 
                padding: 10px;
                font-family: Futura;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFD166;
            }
        """)
        self.btn_clear_all.move(10, 10)
        self.btn_clear_all.setCursor(Qt.PointingHandCursor)
        
        self.btn_clear_all.clicked.connect(self.clear_scene_action)

    def clear_scene_action(self):

        print("Bouton Effacer tout cliqué !")
       

    #clique sur les boutons
    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        item_under_mouse = self.scene.itemAt(pos, self.transform())

        if event.button() == Qt.LeftButton:
            if self.mode == 'place':
                backend_p = self.main_window.create_place_at(pos.x(), pos.y())
                self.main_window.update_properties(backend_p['item'])
            elif self.mode == 'transition':
                backend_t = self.main_window.create_transition_at(pos.x(), pos.y())
                self.main_window.update_properties(backend_t['item'])
            elif self.mode == 'arc':
                if isinstance(item_under_mouse, (PlaceItem, TransitionItem)):
                    if self.temp_arc_start is None:
                        self.temp_arc_start = item_under_mouse
                    else:
                        start = self.temp_arc_start
                        end = item_under_mouse
                        if type(start) != type(end):
                            arc_info = self.main_window.create_arc_between(start, end)
                            if arc_info:
                                self.main_window.update_properties(arc_info['visual'])
                        self.temp_arc_start = None
                else:
                    self.temp_arc_start = None

            if item_under_mouse:
                parent = item_under_mouse.parentItem()
                if parent and isinstance(parent, (PlaceItem, TransitionItem)):
                    item_under_mouse = parent
                self.main_window.update_properties(item_under_mouse)
            else:
                self.main_window.clear_properties()

        super().mousePressEvent(event)


class MainWindow(QWidget):
    def __init__(self, petri_net):
        super().__init__()
        self.net = petri_net
        #self.sim = simulation
        
        #si on est dans le mode d'ajout ou non
        self.active_button = None 

        #style en fonction du mode
        self.STYLE_DEFAULT = """
            QPushButton {
                background-color: #EF476F; 
                border-radius: 10px; 
                color: white;
                font-family: Futura;
                font-size: 12pt;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #ff7096;
            }
        """
        
        self.STYLE_ACTIVE = """
            QPushButton {
                background-color: #710921; 
                border-radius: 10px; 
                color: white; 
                font-weight: bold;
                font-family: Futura;
                font-size: 12pt;
                border: 2px solid #EF476F;
                min-height: 40px;
            }
        """

        # 3eme style pour mettre les noms des places transitions et des arc en noir
        self.STYLE_TEXT_BLACK = "color: black; font-weight: bold; font-family: Futura; border: none;"

        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowTitle("Petri Editor (integrated)")
        self.setStyleSheet("background-color: #073B4C;")

        # Layout principal horizontal
        self.main_layout = QHBoxLayout(self)

        self.view = PetriGraphicsView(self)
        self.view.setParent(self)
        self.view.setStyleSheet("background-color: white; border-radius: 10px;")
        self.main_layout.addWidget(self.view, stretch=4)

        # Layout menu vertical à droite
        self.right_menu = QVBoxLayout()
        self.right_menu.setSpacing(20)

        #frame pour mettre boutons
        self.frame_button = QFrame()
        self.frame_button.setFixedWidth(320)
        self.frame_button.setStyleSheet("background-color: #FFD166; border-radius: 10px;")
        self.btn_layout = QVBoxLayout(self.frame_button)

        #bouton ajout place
        self.buttonPlace = QPushButton("Ajouter une place")
        self.buttonPlace.setStyleSheet(self.STYLE_DEFAULT)

        #bouton ajout transition
        self.buttonTransition = QPushButton("Ajouter une Transition")
        self.buttonTransition.setStyleSheet(self.STYLE_DEFAULT)

        #bouton ajout arc
        self.buttonArc = QPushButton("Ajouter un Arc")
        self.buttonArc.setStyleSheet(self.STYLE_DEFAULT)

        self.btn_layout.addWidget(self.buttonPlace)
        self.btn_layout.addWidget(self.buttonTransition)
        self.btn_layout.addWidget(self.buttonArc)
        self.right_menu.addWidget(self.frame_button)

        #frame pour mettre les infos des places, transitions et arcs
        self.frame_info = QFrame()
        self.frame_info.setFixedWidth(320)
        self.frame_info.setMinimumHeight(350)
        self.frame_info.setStyleSheet("background-color: #FFD166; border-radius: 15px;")
        self.info_layout = QFormLayout(self.frame_info)
        self.info_layout.setContentsMargins(20, 20, 20, 20)
        self.right_menu.addWidget(self.frame_info)

        #frame pour le bouton d'espace d'état 
        self.frame_state = QFrame()
        self.frame_state.setFixedWidth(320)
        self.frame_state.setStyleSheet("background-color: #FFD166; border-radius: 10px;")
        self.state_v_layout = QVBoxLayout(self.frame_state)

        self.buttonState = QPushButton("Génerer les espaces d'états")
        self.buttonState.setStyleSheet(self.STYLE_DEFAULT)

        self.buttonLoad = QPushButton("Load")
        self.buttonLoad.setStyleSheet(self.STYLE_DEFAULT)

        self.buttonSave = QPushButton("Save")
        self.buttonSave.setStyleSheet(self.STYLE_DEFAULT)
        self.buttonSave.clicked.connect(self.save_action)

        self.buttonRapport = QPushButton("Génerer un rapport")
        self.buttonRapport.setStyleSheet(self.STYLE_DEFAULT)

        self.state_v_layout.addWidget(self.buttonState)
        self.state_v_layout.addWidget(self.buttonLoad)
        self.state_v_layout.addWidget(self.buttonSave)
        self.state_v_layout.addWidget(self.buttonRapport)
        
        self.right_menu.addWidget(self.frame_state)
        self.right_menu.addStretch()

        self.main_layout.addLayout(self.right_menu)

        self.buttonPlace.clicked.connect(lambda: self.handle_mode_click('place', self.buttonPlace))
        self.buttonTransition.clicked.connect(lambda: self.handle_mode_click('transition', self.buttonTransition))
        self.buttonArc.clicked.connect(lambda: self.handle_mode_click('arc', self.buttonArc))

        self.visual_places = {}
        self.visual_transitions = {}
        self.visual_arcs = []

    
    # sauvegarde du réseau de Petri a partir d'une fonction de updownload
    def save_action(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Petri Net",
            "",
            "Petri Net (*.json)"
        )

        if not filename:
            return

        save_petri_net(
            filename = filename,
            scene = self.view.scene,
            net = self.net
        )
    

    def handle_mode_click(self, mode, button):

        # désactivation du mode ajout
        if self.active_button == button:
            self.view.set_mode(None)     # retour au mode sélection par défaut
            button.setStyleSheet(self.STYLE_DEFAULT) # retour à la couleur rose
            self.active_button = None    # plus aucun bouton actif
            print("Mode: Sélection / Déplacement")

        # activation du mode ajout
        else:
            if self.active_button:
                self.active_button.setStyleSheet(self.STYLE_DEFAULT)
            
            # activation du bouton
            self.view.set_mode(mode)
            
            button.setStyleSheet(self.STYLE_ACTIVE) 
            self.active_button = button # on mémorise que c'est lui l'actif
            print(f"Mode: Ajout de {mode}")


    def create_place_at(self, x, y):
        # create backend place then visual
        backend_place = self.net.add_place()
        backend_place.initial_tokens = 0
        backend_place.tokens = 0
        item = PlaceItem(x, y, name=backend_place.name)
        # Activation du style noir pour le nom
        if hasattr(item, 'setStyleSheet'): item.setStyleSheet(self.STYLE_TEXT_BLACK)
        self.view.scene.addItem(item)
        self.visual_places[backend_place.name] = item
        return {'backend': backend_place, 'item': item}

    def create_transition_at(self, x, y):
        backend_t = self.net.add_transition()
        item = TransitionItem(x, y, name=backend_t.name)
        # Activation du style noir pour le nom
        if hasattr(item, 'setStyleSheet'): item.setStyleSheet(self.STYLE_TEXT_BLACK)
        self.view.scene.addItem(item)
        self.visual_transitions[backend_t.name] = item
        return {'backend': backend_t, 'item': item}

    def create_arc_between(self, start_item, end_item):
        # determine names for add_arc
        a = start_item.name
        b = end_item.name
        # call backend add_arc. It infers direction
        try:
            arc_backend = self.net.add_arc(a, b)
        except Exception as e:
            print("Arc creation failed:", e)
            return None

        # create visual arc
        visual = ArcItem(start_item, end_item, weight=arc_backend.weight, arc=arc_backend)
        # Activation du style noir pour l'arc
        if hasattr(visual, 'setStyleSheet'): visual.setStyleSheet(self.STYLE_TEXT_BLACK)
        self.view.scene.addItem(visual)
        # link visual to nodes
        start_item.add_arc(visual)
        end_item.add_arc(visual)
        self.visual_arcs.append(visual)
        return {'backend': arc_backend, 'visual': visual}

    # properties panel
    def clear_properties(self):
        while self.info_layout.count():
            item = self.info_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def delete_item(self, item):
        if isinstance(item, (PlaceItem, TransitionItem)):
            # remove backend object too
            name = item.name
            if isinstance(item, PlaceItem):
                self.net.delete_place(name)
                self.visual_places.pop(name, None)
            else:
                self.net.delete_transition(name)
                self.visual_transitions.pop(name, None)

            for arc in item.arcs[:]:
                if arc in self.view.scene.items():
                    self.view.scene.removeItem(arc)
                other = arc.start_item if arc.start_item != item else arc.end_item
                other.remove_arc(arc)
            self.view.scene.removeItem(item)

        elif isinstance(item, ArcItem):
            # remove backend arc
            self.net.arcs = [a for a in self.net.arcs if not (
                (a.place.name == item.start_item.name and a.transition.name == item.end_item.name) or
                (a.place.name == item.end_item.name and a.transition.name == item.start_item.name))]

            item.start_item.remove_arc(item)
            item.end_item.remove_arc(item)
            self.view.scene.removeItem(item)

        self.clear_properties()
        self.view.scene.update()

    def update_properties(self, item):
        self.clear_properties()
        
        # TITRE PROPRIETES
        lbl_prop = QLabel("PROPRIÉTÉS")
        lbl_prop.setAlignment(Qt.AlignCenter)
        lbl_prop.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 16pt; margin-bottom: 10px; text-decoration: underline;")
        self.info_layout.addRow(lbl_prop)

        if isinstance(item, PlaceItem):
            # ID au dessus
            lbl_id = QLabel(f"ID : {item.name}")
            lbl_id.setAlignment(Qt.AlignCenter)
            lbl_id.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 13pt;")
            self.info_layout.addRow(lbl_id)

            # Type d'objet en dessous de l'ID
            lbl_type = QLabel("TYPE : PLACE")
            lbl_type.setAlignment(Qt.AlignCenter)
            lbl_type.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 10pt; color: #444; margin-bottom: 10px;")
            self.info_layout.addRow(lbl_type)

            # Sélecteur [-] Jeton [+]
            layout_jetons = QHBoxLayout()
            btn_moins = QPushButton("-")
            btn_plus = QPushButton("+")
            lbl_jeton = QLabel(f"{item.tokens} Jeton{'s' if item.tokens > 1 else ''}")
            
            style_btn = "QPushButton { background-color: transparent; color: black; font-size: 20pt; font-weight: bold; border: 2px solid black; border-radius: 5px; min-width: 40px; } QPushButton:hover { background-color: #e6bc5c; }"
            btn_moins.setStyleSheet(style_btn)
            btn_plus.setStyleSheet(style_btn)
            lbl_jeton.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 12pt;")
            lbl_jeton.setAlignment(Qt.AlignCenter)

            def incrementer():
                v = item.tokens + 1
                self.net.set_tokens(item.name, v)
                item.set_tokens(v)
                lbl_jeton.setText(f"{v} Jeton{'s' if v > 1 else ''}")

            def decrementer():
                if item.tokens > 0:
                    v = item.tokens - 1
                    self.net.set_tokens(item.name, v)
                    item.set_tokens(v)
                    lbl_jeton.setText(f"{v} Jeton{'s' if v > 1 else ''}")

            btn_plus.clicked.connect(incrementer)
            btn_moins.clicked.connect(decrementer)

            layout_jetons.addWidget(btn_moins)
            layout_jetons.addStretch()
            layout_jetons.addWidget(lbl_jeton)
            layout_jetons.addStretch()
            layout_jetons.addWidget(btn_plus)
            
            container = QWidget()
            container.setLayout(layout_jetons)
            self.info_layout.addRow(container)

        elif isinstance(item, TransitionItem):
            lbl_id = QLabel(f"ID : {item.name}")
            lbl_id.setAlignment(Qt.AlignCenter)
            lbl_id.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 13pt;")
            self.info_layout.addRow(lbl_id)

            lbl_type = QLabel("TYPE : TRANSITION")
            lbl_type.setAlignment(Qt.AlignCenter)
            lbl_type.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 10pt; color: #444;")
            self.info_layout.addRow(lbl_type)

        elif isinstance(item, ArcItem):
            lbl_id = QLabel("ARC")
            lbl_id.setAlignment(Qt.AlignCenter)
            lbl_id.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 13pt;")
            self.info_layout.addRow(lbl_id)

            lbl_type = QLabel("TYPE : LIAISON")
            lbl_type.setAlignment(Qt.AlignCenter)
            lbl_type.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 10pt; color: #444;")
            self.info_layout.addRow(lbl_type)
            
            layout_poids = QHBoxLayout()
            btn_m = QPushButton("-")
            btn_p = QPushButton("+")
            lbl_p = QLabel(f"Poids: {item.weight}")
            
            btn_m.setStyleSheet("QPushButton { background-color: transparent; color: black; font-size: 18pt; font-weight: bold; border: 2px solid black; border-radius: 5px; min-width: 35px; }")
            btn_p.setStyleSheet("QPushButton { background-color: transparent; color: black; font-size: 18pt; font-weight: bold; border: 2px solid black; border-radius: 5px; min-width: 35px; }")
            lbl_p.setStyleSheet(self.STYLE_TEXT_BLACK + "font-size: 11pt;")
            
            def upd_arc(delta):
                nv = max(1, item.weight + delta)
                item.set_weight(nv)
                for a in self.net.arcs:
                    if (a.place.name == item.start_item.name and a.transition.name == item.end_item.name) or (a.place.name == item.end_item.name and a.transition.name == item.start_item.name):
                        a.weight = nv
                        break
                lbl_p.setText(f"Poids: {nv}")

            btn_p.clicked.connect(lambda: upd_arc(1))
            btn_m.clicked.connect(lambda: upd_arc(-1))

            layout_poids.addWidget(btn_m)
            layout_poids.addWidget(lbl_p)
            layout_poids.addWidget(btn_p)
            c_p = QWidget()
            c_p.setLayout(layout_poids)
            self.info_layout.addRow(c_p)

        # BOUTON SUPPRIMER
        btn_delete = QPushButton("SUPPRIMER")
        btn_delete.setStyleSheet("QPushButton { background-color: transparent; color: black; font-weight: bold; font-family: Futura; border: 2px solid black; border-radius: 8px; padding: 10px; margin-top: 20px; } QPushButton:hover { background-color: black; color: #FFD166; }")
        btn_delete.clicked.connect(lambda: self.delete_item(item))
        self.info_layout.addRow(btn_delete)