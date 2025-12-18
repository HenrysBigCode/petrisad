# gui/main_window.py
# Point d'entrée principal de l'interface graphique

from PyQt5.QtWidgets import (QWidget, QFrame, QPushButton,
                             QFormLayout, QLabel, QSpinBox, QHBoxLayout, QVBoxLayout,
                             QGraphicsView, QGraphicsScene, QFileDialog, QInputDialog, QComboBox, QApplication)
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt
from gui.items import PlaceItem, TransitionItem, ArcItem
from logic.updownload import save_petri_net, load_petri_net
from logic.report_gen import generate_pdf_report


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
        # Calcul dynamique de la taille selon l'écran pour voir la barres des taches
        screen = QApplication.primaryScreen().availableGeometry()
        
        # On utilise 90% de la largeur et 80% de la hauteur disponible pour ne pas déborder
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.8) 
        
        # Centrage automatique de la fenêtre
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        
        self.setGeometry(x, y, width, height)
        self.setWindowTitle("Petri Editor (integrated)")
        self.setStyleSheet("background-color: #073B4C;")

        self.main_layout = QHBoxLayout(self) # SUS
        self.view = PetriGraphicsView(self)
        self.view.setStyleSheet("background-color: white; border-radius: 10px;")
        self.main_layout.addWidget(self.view, stretch=4)

        self.layout_menu = QVBoxLayout()
        self.layout_menu.setSpacing(15) # Réduction de l'espacement pour gagner de la hauteur

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
        # CHANGEMENT : On baisse le MinimumHeight à 250 pour permettre à la fenêtre de rétrécir
        self.frame_info.setMinimumHeight(250) 
        self.frame_info.setStyleSheet("background-color: #FFD166; border-radius: 15px;")
        self.info_layout = QFormLayout(self.frame_info)
        self.info_layout.setContentsMargins(20, 20, 20, 20)
        self.layout_menu.addWidget(self.frame_info)

        self.frame_state = QFrame()
        self.frame_state.setFixedWidth(320)
        self.frame_state.setStyleSheet("background-color: #FFD166; border-radius: 10px;")
        self.state_v_layout = QVBoxLayout(self.frame_state)

        self.buttonColorAlgo = QPushButton("Coloration Graphe (CPN)")
        self.buttonColorAlgo.clicked.connect(self.apply_algorithmic_coloring)
        self.buttonState = QPushButton("Génerer les espaces d'états")
        self.buttonState.clicked.connect(self.show_state_space_popup) # Connexion de la simulation
        self.buttonLoad = QPushButton("Load")
        self.buttonLoad.clicked.connect(self.load_action)
        self.buttonSave = QPushButton("Save")
        self.buttonSave.clicked.connect(self.save_action)
        self.buttonRapport = QPushButton("Génerer un rapport")
        self.buttonRapport.clicked.connect(self.handle_generate_report)

        for b in [self.buttonColorAlgo, self.buttonState, self.buttonLoad, self.buttonSave, self.buttonRapport]:
            b.setStyleSheet(self.STYLE_DEFAULT)
            self.state_v_layout.addWidget(b)
        
        self.layout_menu.addWidget(self.frame_state)
        self.layout_menu.addStretch()
        self.main_layout.addLayout(self.layout_menu)

        self.buttonPlace.clicked.connect(lambda: self.handle_mode_click('place', self.buttonPlace))
        self.buttonTransition.clicked.connect(lambda: self.handle_mode_click('transition', self.buttonTransition))
        self.buttonArc.clicked.connect(lambda: self.handle_mode_click('arc', self.buttonArc))

        # Bouton Effacer tout sur la scene
        self.buttonClearAll = QPushButton("Effacer tout", self)
        self.buttonClearAll.setStyleSheet("""
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
        self.buttonClearAll.move(20, 20)
        self.buttonClearAll.setCursor(Qt.PointingHandCursor)
        self.buttonClearAll.clicked.connect(self.reset_editor)

        self.visual_places = {}
        self.visual_transitions = {}
        
    def show_state_space_popup(self):
        """Lance la simulation et affiche l'espace d'états en utilisant simulation.py."""
        if not self.net.places and not self.net.transitions:
            print("Erreur : Le réseau est vide.")
            return

        try:
            # Correction de l'import : on va chercher dans simulation.py
            from logic.simulation import StateSpaceVisualizer, build_state_space
            
            # Initialisation du visualiseur
            viz = StateSpaceVisualizer()
            
            # Construction de l'espace d'états
            build_state_space(self.net, viz)
            
            # Lancement de la fenêtre interactive Matplotlib
            viz.show_interactive()
            
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la simulation : {e}")
            import traceback
            traceback.print_exc()

    def handle_generate_report(self):
            print("Bouton Rapport cliqué...")
            if not self.net.places and not self.net.transitions:
                print("Erreur : Réseau vide.")
                return

            filename, _ = QFileDialog.getSaveFileName(self, "Save PDF", "rapport.pdf", "PDF (*.pdf)")
            
            if filename:
                print(f"Destination choisie : {filename}")
                try:
                    from logic.report_gen import generate_pdf_report
                    print("Lancement de generate_pdf_report...")
                    generate_pdf_report(self.net, filename)
                    print("Sauvegarde terminée avec succès")
                except Exception as e:
                    print(f"ERREUR CRITIQUE : {e}")
                    import traceback
                    traceback.print_exc()


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

        success, message, p_items, t_items = load_petri_net(
            filename = filename,
            scene = self.view.scene,
            petri_net = self.net
        )

        if success:
            self.visual_places = p_items
            self.visual_transitions = t_items
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
            while name in self.visual_places:
                name = f"{base_name}.{counter}"
                counter += 1
            
            bp = self.net.add_place(name=name)
            item = PlaceItem(x, y, name=name)
            item.color_set = "Integer" 
            self.view.scene.addItem(item)
            self.visual_places[name] = item
            return {'backend': bp, 'item': item}
        elif ok and not name:
            bp = self.net.add_place()
            item = PlaceItem(x, y, name=bp.name)
            item.color_set = "Integer" 
            self.view.scene.addItem(item)
            self.visual_places[bp.name] = item
            return {'backend': bp, 'item': item}
        else:
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
        elif ok and not name:
            bt = self.net.add_transition()
            item = TransitionItem(x, y, name=bt.name)
            self.view.scene.addItem(item)
            self.visual_transitions[bt.name] = item
            return {'backend': bt, 'item': item}
        else:
            return None
    
    def create_arc_between(self, start_item, end_item):
        try:
            arc_backend = self.net.add_arc(start_item.name, end_item.name)
            visual = ArcItem(start_item, end_item, weight=arc_backend.weight, arc=arc_backend)
            self.view.scene.addItem(visual)
            start_item.add_arc(visual)
            end_item.add_arc(visual)
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
            
        elif isinstance(item, ArcItem):
            self.info_layout.addRow(QLabel("TYPE : ARC / LIAISON", styleSheet=style_noir))
            
            # Affichage et modification du POIDS de l'arc
            self.info_layout.addRow(QLabel("POIDS DE L'ARC :", styleSheet=style_noir))
            
            layout_poids = QHBoxLayout()
            btn_moins_p = QPushButton("-")
            btn_plus_p = QPushButton("+")
            
            # On utilise le même style "XL" que pour les jetons
            style_btn_xl = "QPushButton { background-color: transparent; color: black; font-size: 24pt; font-weight: bold; border: 3px solid black; border-radius: 8px; min-width: 60px; min-height: 50px; } QPushButton:hover { background-color: #e6bc5c; }"
            btn_moins_p.setStyleSheet(style_btn_xl)
            btn_plus_p.setStyleSheet(style_btn_xl)
            
            lbl_poids = QLabel(str(item.weight))
            lbl_poids.setAlignment(Qt.AlignCenter)
            lbl_poids.setStyleSheet(style_noir + "font-size: 20pt;")
            
            def adjust_weight(delta):
                new_weight = max(1, item.weight + delta)
                item.set_weight(new_weight) # Met à jour le visuel
                item.backend_arc.weight = new_weight # Met à jour le poids dans le backend (PetriNet)
                lbl_poids.setText(str(new_weight))

            btn_plus_p.clicked.connect(lambda: adjust_weight(1))
            btn_moins_p.clicked.connect(lambda: adjust_weight(-1))
            
            layout_poids.addWidget(btn_moins_p)
            layout_poids.addStretch()
            layout_poids.addWidget(lbl_poids)
            layout_poids.addStretch()
            layout_poids.addWidget(btn_plus_p)
            
            container_p = QWidget()
            container_p.setLayout(layout_poids)
            self.info_layout.addRow(container_p)
        

        btn_del = QPushButton("SUPPRIMER")
        btn_del.setStyleSheet("background-color: transparent; color: black; font-weight: bold; border: 2px solid black; border-radius: 8px; padding: 10px; margin-top: 20px;")
        btn_del.clicked.connect(lambda: self.delete_item(item)) 
        self.info_layout.addRow(btn_del)


    # applique la coloration algorithmique CPN
    def apply_algorithmic_coloring(self):
        palette = {
            "Integer": QColor("#118AB2"), "String": QColor("#06D6A0"),
            "Boolean": QColor("#FFD166"), "Complex": QColor("#EF476F"),
            "Guard": QColor("#073B4C")
        }
        coloring_map = {}
        
        for p in self.net.places:
            name = p.name if hasattr(p, 'name') else str(p)
            # On récupère le type de donnée de la place
            coloring_map[name] = getattr(p, 'color_set', 'Integer')

        # Les transitions sont marquées comme ayant des expressions de Garde (G)
        for t in self.net.transitions:
            name = t.name if hasattr(t, 'name') else str(t)
            coloring_map[name] = "Guard"
        
        for name, data_type in coloring_map.items():
            item = self.visual_places.get(name) or self.visual_transitions.get(name)
            if item:
                final_type = getattr(item, 'color_set', data_type)
                item.setBrush(QBrush(palette.get(final_type, QColor("#CCCCCC"))))
                item.setPen(QPen(Qt.white, 1, Qt.DashLine) if final_type == "Guard" else QPen(Qt.black, 2))
        self.view.scene.update()
        print("Coloration CPN appliquée.")