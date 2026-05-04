# Système de Surveillance Énergétique Intelligente (Smart Energy Monitoring)

## Description du Projet
Ce projet consiste en une solution IoT complète dédiée à la surveillance et à la gestion automatisée de la consommation énergétique. Le système permet de collecter des données de puissance en temps réel, de détecter des anomalies de consommation (surcharges) et d'agir instantanément sur l'infrastructure via un mécanisme de délestage automatique.

## Fonctionnalités Principales
- Surveillance en temps réel de la puissance (W), de l'intensité (A) et de la tension (V).
- Détection automatique de surcharge avec un seuil configurable (300W).
- Système de délestage automatisé via le contrôle d'un relais.
- Historisation des mesures et des alertes sur une base de données cloud.
- Interface de contrôle et de visualisation double (Node-RED Dashboard et Dashboard Web dédié).

## Architecture du Système
L'architecture repose sur une communication bidirectionnelle utilisant le protocole MQTT :
1. **Couche Edge (Simulation)** : Un script Python simulant un ESP32 (Digital Twin) génère les données de consommation et reçoit les commandes de contrôle.
2. **Couche Transport** : Utilisation d'un broker MQTT local (Mosquitto) pour l'échange de messages asynchrones.
3. **Couche Logique** : Node-RED traite les flux de données, applique les règles métier et orchestre les communications avec les services tiers.
4. **Couche Stockage** : Firebase Realtime Database assure la persistance des données et des événements critiques.
5. **Couche Présentation** : Dashboards interactifs permettant le suivi en temps réel et le contrôle manuel du système.

## Structure du Projet
- **simulateur/** : Script Python simulant le comportement de l'ESP32 et de ses capteurs.
- **nodered/** : Fichiers de configuration et flux JSON pour l'orchestration du système.
- **dashboard/** : Interface utilisateur HTML/JavaScript connectée à Firebase.
- **wokwi/** : Simulation matérielle incluant le schéma du circuit et le code source Arduino (C++).

## Guide d'Installation

### 1. Préparation de l'environnement Python
Pour exécuter le simulateur, il est nécessaire d'installer les dépendances requises :
```powershell
cd simulateur
python -m venv venv
.\venv\Scripts\activate
pip install paho-mqtt
```

### 2. Lancement du Système
Le déploiement complet nécessite l'exécution des composants suivants :
- **Broker MQTT** : Assurez-vous que le service Mosquitto est actif localement.
- **Simulateur ESP32** : Exécutez `python simulateur_esp32.py` depuis le dossier simulateur.
- **Node-RED** : Démarrez l'instance Node-RED et déployez le flux contenu dans `flows.json`.
- **Interface Utilisateur** : Accédez au dashboard Node-RED via `http://localhost:1880/ui` ou lancez le serveur web pour `dashboard.html`.

## Logique de Délestage
Le système intègre une logique de protection intelligente :
- **Seuil d'alerte** : 300W.
- **Action corrective** : En cas de dépassement, le relais est immédiatement ouvert pour couper la charge.
- **Hystérésis** : Pour éviter les commutations rapides, le réarmement automatique ne s'effectue que lorsque la puissance redescend sous 270W.
- **Priorité** : Les commandes manuelles via le dashboard restent prioritaires sur la logique automatique.

## Spécifications Techniques
- **Protocole** : MQTT (QoS 1).
- **Format de données** : JSON.
- **Base de données** : Firebase Realtime DB.
- **Outils de développement** : Python 3.x, Node-RED v4.x, Mosquitto.


