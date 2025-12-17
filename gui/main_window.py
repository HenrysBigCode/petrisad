# gui/main_window.py
import math
from PyQt5.QtWidgets import (QWidget, QFrame, QPushButton,
                             QFormLayout, QLabel, QSpinBox)
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog

from gui.items import PlaceItem, TransitionItem, ArcItem
from logic.updownload import save_petri_net, load_petri_net


class PetriGraphicsView(QGraphicsView):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setSceneRect(0, 0, 1000, 1100)
        self.setRenderHints(QPainter.Antialiasing)
        self.mode = None
        self.temp_arc_start = None

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
                                self.scene.addItem(arc_info['visual'])
                                start.add_arc(arc_info['visual'])
                                end.add_arc(arc_info['visual'])
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
        
        # si on est dans le mode d'ajout ou non
        self.active_button = None 

        # style en fonction du mode
        self.STYLE_DEFAULT = """
            QPushButton {
                background-color: #EF476F; 
                border-radius: 10px; 
                color: whit;
                font-family: Futura;
                font-size: 12pt;
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
            }
        """

        self.initUI()


    def initUI(self):
        self.setGeometry(100, 100, 1020, 650)
        self.setWindowTitle("Petri Editor (integrated)")

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


        self.view = PetriGraphicsView(self)
        self.view.setParent(self)
        self.view.setGeometry(20, 20, 680, 760)

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
        self.view.scene.addItem(item)
        self.visual_places[backend_place.name] = item
        return {'backend': backend_place, 'item': item}

    def create_transition_at(self, x, y):
        backend_t = self.net.add_transition()
        item = TransitionItem(x, y, name=backend_t.name)
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
                self.view.scene.removeItem(arc)
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
        lbl_title = QLabel("Propriétés")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        lbl_title_font = QFont("Futura", 12)
        lbl_title.setFont(lbl_title_font)
        palette = lbl_title.palette()
        palette.setColor(QPalette.WindowText, QColor("#FFFFFF"))
        lbl_title.setPalette(palette)
        self.info_layout.addRow(lbl_title)

        if isinstance(item, PlaceItem):
            self.info_layout.addRow(QLabel(f"Type: Place ({item.name})"))
            spin_tokens = QSpinBox()
            spin_tokens.setRange(0, 99)
            # backend token value:
            backend_p = self.net.places.get(item.name)
            spin_tokens.setValue(backend_p.tokens if backend_p else item.tokens)
            def on_token_change(v):
                # update backend then visual
                self.net.set_tokens(item.name, v)
                item.set_tokens(v)
            spin_tokens.valueChanged.connect(on_token_change)
            self.info_layout.addRow("Jetons :", spin_tokens)

        elif isinstance(item, TransitionItem):
            self.info_layout.addRow(QLabel(f"Type: Transition ({item.name})"))

        elif isinstance(item, ArcItem):
            self.info_layout.addRow(QLabel("Type: Arc"))
            spin_weight = QSpinBox()
            spin_weight.setRange(1, 999)
            spin_weight.setValue(item.weight)
            def on_weight_change(v):
                item.set_weight(v)
                # update backend arc weight
                # find the backend arc and update
                for arc in self.net.arcs:
                    if arc.place.name == item.start_item.name and arc.transition.name == item.end_item.name:
                        arc.weight = v
                        break
                    if arc.place.name == item.end_item.name and arc.transition.name == item.start_item.name:
                        arc.weight = v
                        break
            spin_weight.valueChanged.connect(on_weight_change)
            self.info_layout.addRow("Poids :", spin_weight)

        btn_delete = QPushButton("Supprimer")
        btn_delete.setStyleSheet("background-color: #ffcccc; color: red; font-weight: bold; border-radius: 5px;")
        btn_delete.clicked.connect(lambda: self.delete_item(item))
        self.info_layout.addRow(btn_delete)
