# gui/main_window.py
import math
from PyQt5.QtWidgets import (QWidget, QFrame, QPushButton,
                             QFormLayout, QLabel, QSpinBox, QHBoxLayout, QVBoxLayout,
                             QGraphicsView, QGraphicsScene, QFileDialog, QInputDialog, QComboBox)
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt
from gui.items import PlaceItem, TransitionItem, ArcItem
from logic.updownload import save_petri_net, load_petri_net
from logic.coloring import get_graph_coloring


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

        # Bouton Effacer tout sur la scene
        self.btn_clear_all = QPushButton("Effacer tout", self)
        self.btn_clear_all.setStyleSheet("""
            QPushButton {
                background-color: #EF476F; 
                color: white; 
                border-radius: 5px; 
                padding: 8px;
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

    # définit le mode d'ajout
    def set_mode(self, mode):
        self.mode = mode
        self.temp_arc_start = None
        if mode is None:
            self.setDragMode(QGraphicsView.RubberBandDrag) 
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(Qt.CrossCursor)

    def clear_scene_action(self):
        print("Bouton Effacer tout cliqué !")

    #clique sur les boutons
    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        item_under_mouse = self.scene.itemAt(pos, self.transform())

        if event.button() == Qt.LeftButton:
            if self.mode == 'place':
                res = self.main_window.create_place_at(pos.x(), pos.y())
                if res:
                    self.main_window.update_properties(res['item'])
            elif self.mode == 'transition':
                res = self.main_window.create_transition_at(pos.x(), pos.y())
                if res:
                    self.main_window.update_properties(res['item'])
            elif self.mode == 'arc':
                if item_under_mouse:
                    target = item_under_mouse
                    if target.parentItem() and isinstance(target.parentItem(), (PlaceItem, TransitionItem)):
                        target = target.parentItem()

                    if isinstance(target, (PlaceItem, TransitionItem)):
                        if self.temp_arc_start is None:
                            self.temp_arc_start = target
                        else:
                            start = self.temp_arc_start
                            end = target
                            if type(start) != type(end):
                                arc_info = self.main_window.create_arc_between(start, end)
                                if arc_info:
                                    self.main_window.update_properties(arc_info['visual'])
                            self.temp_arc_start = None
                else:
                    self.temp_arc_start = None

            if item_under_mouse:
                target = item_under_mouse
                if target.parentItem() and isinstance(target.parentItem(), (PlaceItem, TransitionItem)):
                    target = target.parentItem()
                self.main_window.update_properties(target)
            else:
                self.main_window.clear_properties()

        super().mousePressEvent(event)


class MainWindow(QWidget):
    def __init__(self, petri_net):
        super().__init__()
        self.net = petri_net
        self.active_button = None 

        self.STYLE_DEFAULT = """
            QPushButton {
                background-color: #EF476F; 
                border-radius: 10px; 
                color: white;
                font-family: Futura;
                font-size: 12pt;
                min-height: 40px;
            }
            QPushButton:hover { background-color: #ff7096; }
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

        self.initUI()


    def initUI(self):
        self.setGeometry(0, 0, 1920, 1080)
        self.setWindowTitle("Petri Editor (integrated)")
        self.setStyleSheet("background-color: #073B4C;")

        """
        #frame pour mettre boutons
        self.frame_button = QFrame(self)
        self.frame_button.setGeometry(720, 20, 280, 250)
        self.frame_button.setStyleSheet("background-color: #FFD166; border-radius: 10px;")

        #bouton ajout place
        self.buttonPlace = QPushButton("Ajouter une place", self.frame_button)
        self.buttonPlace.setGeometry(20, 20, 240, 40)
        self.buttonPlace.setStyleSheet(self.STYLE_DEFAULT)

        #bouton ajout transition
        self.buttonTransition = QPushButton("Ajouter une Transition", self.frame_button)
        self.buttonTransition.setGeometry(20, 80, 240, 40)
        self.buttonTransition.setStyleSheet(self.STYLE_DEFAULT)

        #bouton ajout arc
        self.buttonArc = QPushButton("Ajouter un Arc", self.frame_button)
        self.buttonArc.setGeometry(20, 140, 240, 40)
        self.buttonArc.setStyleSheet(self.STYLE_DEFAULT)

        #frame pour mettre les infos des places, transitions et arcs
        self.frame_info = QFrame(self)
        self.frame_info.setGeometry(720, 290, 280, 150)
        self.frame_info.setStyleSheet("background-color: #FFD166; border-radius: 10px;")
        self.info_layout = QFormLayout(self.frame_info)

        #frame pour le bouton d'espace d'état 
        self.frame_state = QFrame(self)
        self.frame_state.setGeometry(720, 460, 280, 250)
        self.frame_state.setStyleSheet("background-color: #FFD166; border-radius: 10px;")
        self.state_layout = QFormLayout(self.frame_state)

        self.buttonState = QPushButton("Génerer les espaces d'états", self.frame_state)
        self.buttonState.setGeometry(20, 20, 240, 40)
        self.buttonState.setStyleSheet(self.STYLE_DEFAULT)

        self.buttonLoad = QPushButton("Load", self.frame_state)
        self.buttonLoad.setGeometry(20, 80, 240, 40)
        self.buttonLoad.setStyleSheet(self.STYLE_DEFAULT)
        self.buttonLoad.clicked.connect(self.load_action)

        self.buttonSave = QPushButton("Save", self.frame_state)
        self.buttonSave.setGeometry(20, 140, 240, 40)
        self.buttonSave.setStyleSheet(self.STYLE_DEFAULT)
        self.buttonSave.clicked.connect(self.save_action)

        self.buttonRapport = QPushButton("Génerer un rapport", self.frame_state)
        self.buttonRapport.setGeometry(20, 200, 240, 40)
        self.buttonRapport.setStyleSheet(self.STYLE_DEFAULT)
        self.buttonRapport.clicked.connect(self.reset_editor)
        """

        self.main_layout = QHBoxLayout(self) # SUS
        self.view = PetriGraphicsView(self)
        self.view.setStyleSheet("background-color: white; border-radius: 10px;")
        self.main_layout.addWidget(self.view, stretch=4)

        self.layout_menu = QVBoxLayout()
        self.layout_menu.setSpacing(20)

        self.frame_button = QFrame()
        self.frame_button.setFixedWidth(320)
        self.frame_button.setStyleSheet("background-color: #FFD166; border-radius: 10px;")
        self.btn_layout = QVBoxLayout(self.frame_button)

        self.buttonPlace = QPushButton("Ajouter une place")
        self.buttonTransition = QPushButton("Ajouter une Transition")
        self.buttonArc = QPushButton("Ajouter un Arc")

        for b in [self.buttonPlace, self.buttonTransition, self.buttonArc]:
            b.setStyleSheet(self.STYLE_DEFAULT)
            self.btn_layout.addWidget(b)

        self.layout_menu.addWidget(self.frame_button)

        self.frame_info = QFrame()
        self.frame_info.setFixedWidth(320)
        self.frame_info.setMinimumHeight(400) # Légèrement plus grand
        self.frame_info.setStyleSheet("background-color: #FFD166; border-radius: 15px;")
        self.info_layout = QFormLayout(self.frame_info)
        self.info_layout.setContentsMargins(20, 20, 20, 20)
        self.layout_menu.addWidget(self.frame_info)

        self.frame_state = QFrame()
        self.frame_state.setFixedWidth(320)
        self.frame_state.setStyleSheet("background-color: #FFD166; border-radius: 10px;")
        self.state_v_layout = QVBoxLayout(self.frame_state)

        self.buttonColorAlgo = QPushButton("Coloration Graphe (CPN)")
        self.buttonState = QPushButton("Génerer les espaces d'états")
        self.buttonLoad = QPushButton("Load")
        self.buttonSave = QPushButton("Save")
        self.buttonRapport = QPushButton("Génerer un rapport")

        for b in [self.buttonColorAlgo, self.buttonState, self.buttonLoad, self.buttonSave, self.buttonRapport]:
            b.setStyleSheet(self.STYLE_DEFAULT)
            self.state_v_layout.addWidget(b)

        self.buttonSave.clicked.connect(self.save_action)
        self.buttonColorAlgo.clicked.connect(self.apply_algorithmic_coloring)
        
        self.layout_menu.addWidget(self.frame_state)
        self.layout_menu.addStretch()
        self.main_layout.addLayout(self.layout_menu)

        self.buttonPlace.clicked.connect(lambda: self.handle_mode_click('place', self.buttonPlace))
        self.buttonTransition.clicked.connect(lambda: self.handle_mode_click('transition', self.buttonTransition))
        self.buttonArc.clicked.connect(lambda: self.handle_mode_click('arc', self.buttonArc))

        self.visual_places = {}
        self.visual_transitions = {}
        self.visual_arcs = []


    # fonction utile pour restet l'éditeur
    def reset_editor(self):
        self.view.scene.clear()  # Clear visual items
        self.net.wipe() # Clear backend
        # Reset editor state
        self.clear_properties()
        self.temp_arc_start = None

    
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
    
    
    # ouverture d'un réseau de Petri a partir d'une fonction de updownload
    def load_action(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Petri Net",
            "",
            "Petri Net (*.json)"
        )

        if not filename:
            return

        # MainWindow owns the wipe
        self.reset_editor()

        success, message = load_petri_net(
            filename = filename,
            scene = self.view.scene,
            petri_net = self.net
        )

        if success:
            print("Petri net loaded")
        else:
            print("Fuck fuck fuckkkk", message)
    
    
    # gestion des clics sur les boutons d'ajout
    def handle_mode_click(self, mode, button):
        # désactivation du mode ajout
        if self.active_button == button:
            self.view.set_mode(None)
            button.setStyleSheet(self.STYLE_DEFAULT)
            self.active_button = None
        else:
            if self.active_button:
                self.active_button.setStyleSheet(self.STYLE_DEFAULT)
            self.view.set_mode(mode)
            button.setStyleSheet(self.STYLE_ACTIVE) 
            self.active_button = button

    def create_place_at(self, x, y):
        name, ok = QInputDialog.getText(self, 'Nouvelle Place', 'Entrez le nom :')
        if ok and name:
            base_name = name
            counter = 1
            while name in self.visual_places or name in self.visual_transitions:
                name = f"{base_name}.{counter}"
                counter += 1
            
            bp = self.net.add_place(name=name)
            item = PlaceItem(x, y, name=name)
            item.color_set = "Integer" 
            self.view.scene.addItem(item)
            self.visual_places[name] = item
            return {'backend': bp, 'item': item}
        return None

    def create_transition_at(self, x, y):
        name, ok = QInputDialog.getText(self, 'Nouvelle Transition', 'Entrez le nom :')
        if ok and name:
            base_name = name
            counter = 1
            while name in self.visual_places or name in self.visual_transitions:
                name = f"{base_name}.{counter}"
                counter += 1
                
            bt = self.net.add_transition(name=name)
            item = TransitionItem(x, y, name=name)
            self.view.scene.addItem(item)
            self.visual_transitions[name] = item
            return {'backend': bt, 'item': item}
        return None
    
    def create_arc_between(self, start_item, end_item):
        try:
            arc_backend = self.net.add_arc(start_item.name, end_item.name)
            visual = ArcItem(start_item, end_item, weight=arc_backend.weight, arc=arc_backend)
            self.view.scene.addItem(visual)
            start_item.add_arc(visual)
            end_item.add_arc(visual)
            self.visual_arcs.append(visual)
            return {'backend': arc_backend, 'visual': visual}
        except: return None

    def clear_properties(self):
        while self.info_layout.count():
            item = self.info_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def delete_item(self, item):
        if isinstance(item, (PlaceItem, TransitionItem)):
            name = item.name
            if isinstance(item, PlaceItem):
                self.net.delete_place(name)
                self.visual_places.pop(name, None)
            else:
                self.net.delete_transition(name)
                self.visual_transitions.pop(name, None)
            for arc in item.arcs[:]:
                if arc in self.view.scene.items(): self.view.scene.removeItem(arc)
                other = arc.start_item if arc.start_item != item else arc.end_item
                other.remove_arc(arc)
            self.view.scene.removeItem(item)
        elif isinstance(item, ArcItem):
            self.net.delete_arc(item.backend_arc.place.name, item.backend_arc.transition.name, item.backend_arc.direction)

            item.start_item.remove_arc(item)
            item.end_item.remove_arc(item)
            self.view.scene.removeItem(item)
        self.clear_properties()
        self.view.scene.update()

    def update_properties(self, item):
        self.clear_properties()
        style_noir = "color: black; font-weight: bold; font-family: Futura; border: none;"
        style_btn_xql = "QPushButton { background-color: transparent; color: black; font-size: 24pt; font-weight: bold; border: 3px solid black; border-radius: 8px; min-width: 60px; min-height: 50px; } QPushButton:hover { background-color: #e6bc5c; }"

        lbl_prop = QLabel("PROPRIÉTÉS")
        lbl_prop.setStyleSheet(style_noir + "font-size: 16pt; text-decoration: underline;")
        self.info_layout.addRow(lbl_prop)

        if isinstance(item, PlaceItem):
            self.info_layout.addRow(QLabel(f"ID : {item.name}", styleSheet=style_noir))
            
            # CHOIX COLOR SET (Pas de coloration auto ici)
            self.info_layout.addRow(QLabel("COLOR SET (Σ) :", styleSheet=style_noir))
            combo = QComboBox()
            combo.addItems(["Integer", "String", "Boolean", "Complex"])
            combo.setCurrentText(getattr(item, 'color_set', 'Integer'))
            combo.setStyleSheet("background-color: white; color: black; border-radius: 5px; padding: 5px;")
            
            def on_type_change(t):
                item.color_set = t
            combo.currentTextChanged.connect(on_type_change)
            self.info_layout.addRow(combo)

            # jetons
            self.info_layout.addRow(QLabel("JETONS :", styleSheet=style_noir))
            layout_j = QHBoxLayout()
            btn_m = QPushButton("-")
            btn_p = QPushButton("+")
            btn_m.setStyleSheet(style_btn_xql)
            btn_p.setStyleSheet(style_btn_xql)
            
            lbl_j = QLabel(f"{item.tokens}")
            lbl_j.setAlignment(Qt.AlignCenter)
            lbl_j.setStyleSheet(style_noir + f"font-size: {'22pt' if item.tokens > 5 else '16pt'};")
            
            def upd(v):
                new_v = max(0, item.tokens + v)
                self.net.set_tokens(item.name, new_v)
                item.set_tokens(new_v)
                lbl_j.setText(f"{new_v}")
                lbl_j.setStyleSheet(style_noir + f"font-size: {'22pt' if new_v > 5 else '16pt'};")

            btn_p.clicked.connect(lambda: upd(1))
            btn_m.clicked.connect(lambda: upd(-1))
            layout_j.addWidget(btn_m); layout_j.addStretch(); layout_j.addWidget(lbl_j); layout_j.addStretch(); layout_j.addWidget(btn_p)
            c = QWidget(); c.setLayout(layout_j); self.info_layout.addRow(c)

        elif isinstance(item, TransitionItem):
            self.info_layout.addRow(QLabel(f"ID : {item.name}", styleSheet=style_noir))

        btn_del = QPushButton("SUPPRIMER")
        btn_del.setStyleSheet("background-color: transparent; color: black; font-weight: bold; border: 2px solid black; border-radius: 8px; padding: 10px; margin-top: 20px;")
        btn_del.clicked.connect(lambda: self.delete_item(item)) 
        self.info_layout.addRow(btn_del)


    def apply_algorithmic_coloring(self):
        palette = {
            "Integer": QColor("#118AB2"), "String": QColor("#06D6A0"),
            "Boolean": QColor("#FFD166"), "Complex": QColor("#EF476F"),
            "Guard": QColor("#073B4C")
        }
        coloring_map = get_graph_coloring(self.net)
        for name, data_type in coloring_map.items():
            item = self.visual_places.get(name) or self.visual_transitions.get(name)
            if item:
                final_type = getattr(item, 'color_set', data_type)
                item.setBrush(QBrush(palette.get(final_type, QColor("#CCCCCC"))))
                item.setPen(QPen(Qt.white, 1, Qt.DashLine) if final_type == "Guard" else QPen(Qt.black, 2))
        self.view.scene.update()
        print("Coloration CPN appliquée.")