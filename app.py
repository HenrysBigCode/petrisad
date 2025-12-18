# app.py

import sys
from PyQt5.QtWidgets import QApplication
from logic.petri_net import PetriNet
from gui.main_window import MainWindow

# Génère le network de Petri et lance l'interface graphique
def main():
    app = QApplication(sys.argv)
    net = PetriNet()
    win = MainWindow(net)
    win.show()
    sys.exit(app.exec_())

# Lance tout le programme
if __name__ == "__main__":
    main()