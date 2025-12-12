# app.py

import sys
from PyQt5.QtWidgets import QApplication
from logic.petri_net import PetriNet
from logic.simulation import Simulation
from gui.main_window import MainWindow

# Génère le network de Petri, la simulation et lance l'interface graphique
def main():
    app = QApplication(sys.argv)
    net = PetriNet()
    sim = Simulation(net)
    win = MainWindow(net, sim)
    win.show()
    sys.exit(app.exec_())

# Lance tout le programme
if __name__ == "__main__":
    main()