# Readme Petri Editor 

## Presentation
Cet outil est un editeur de Reseaux de Petri CPN permettant de modeliser, simuler et analyser graphiquement des systemes complexes. Il inclut un moteur de calcul d espace d etats et une generation de rapports automatisee.

### Fonctionnalites Cles
* Edition Graphique : Ajout de places, transitions et arcs avec gestion des poids.
* Analyse d Accessibilite : Generation de l arbre des etats avec detection des deadlocks en rouge.
* Proprietes Formelles : Verification de la vivacite, de la bornitude et des cycles structurels.
* Export PDF : Generation d un rapport complet incluant le graphe d accessibilite et le diagnostic du reseau.

---

## Installation

### 1. Prerequis
* Python 3.9 ou version superieure.
* Graphviz : Necessaire pour le rendu des graphes en arbre.

Installation de Graphviz :
* macOS : brew install graphviz
* Windows : Telecharger sur le site officiel graphviz.org et cocher Add to PATH pendant l installation.
* Linux : sudo apt-get install graphviz

### 2. Configuration de l environnement
Ouvrez un terminal dans le dossier du projet :

python3 -m venv .venv

Activation de l environnement sur macOS ou Linux :
source .venv/bin/activate

Activation de l environnement sur Windows :
.venv\Scripts\activate

Mise a jour de pip :
pip install --upgrade pip

### 3. Installation des modules
Installez les bibliotheques necessaires :
pip install PyQt5 networkx matplotlib pydot fpdf

---

## Lancement
Pour demarrer l application :
python3 -m app

---

## Utilisation

1. Dessin : Utilisez la sidebar gauche pour selectionner un mode Place, Transition ou Arc. Cliquez sur la scene pour placer les elements.
2. Proprietes : Selectionnez un element pour modifier ses jetons, son nom ou son poids dans le panneau de droite.
3. Simulation : Cliquez sur le bouton Generer les espaces d etats pour voir tous les marquages possibles dans une fenetre interactive.
4. Rapport : Cliquez sur le bouton Generer un rapport pour sauvegarder l analyse complete en format PDF.

---

## Structure du projet
* app.py : Point d entree de l application.
* gui/ : Contient l interface utilisateur, les fenetres et les items graphiques.
* logic/ : Contient la logique interne du reseau, les algorithmes de calcul et le moteur de generation PDF.

---