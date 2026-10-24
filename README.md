# Tankepler

Robot d'exploration piloté depuis un navigateur, qui relève la température, l'humidité, la pression
et la luminosité de l'endroit où il passe. Projet d'école de 2<sup>e</sup> année, en équipe de 4.

**Ma part** : le câblage des capteurs sur le Raspberry Pi et l'interface web (pages de données et de graphiques).

## Matériel

| Élément | Rôle |
| --- | --- |
| Raspberry Pi | Cerveau du robot et serveur web |
| BME280 (I2C, adresse 0x76) | Température, humidité, pression |
| VEML7700 (I2C) | Luminosité, avec réglage automatique de la sensibilité |
| L298N + 2 moteurs | Déplacement, vitesse réglée en PWM |

## Ce que fait le serveur (`server.py`, Flask)

- Lit les capteurs toutes les 5 secondes et enregistre chaque mesure dans un fichier CSV
- `/data` : tableau des mesures, `/graph` : graphiques, `/download-csv` : export
- `/data.json` : les dernières mesures pour l'interface
- `/events` : flux en direct des mesures (Server-Sent Events)
- `/move` et `/stop` : pilotage des moteurs

## Organisation

| Fichier | Rôle |
| --- | --- |
| `server.py` | Serveur Flask : capteurs, enregistrement CSV, API, pilotage |
| `component/motor_control.py` | Classe `RobotMotors` (gpiozero) : avancer, reculer, tourner, vitesse |
| `templates/data.html`, `templates/graph.html` | Pages de données et de graphiques |
| `static/style.css` | Style de l'interface |
| `tests-capteurs/` | Scripts de test de chaque capteur et des moteurs, utilisés pendant le câblage |

La page d'accueil de pilotage (`templates/index.html`) n'a pas été conservée.

## Lancer (sur le Raspberry Pi)

```bash
pip install flask gpiozero adafruit-circuitpython-bme280 adafruit-circuitpython-veml7700
python server.py
```

Puis ouvrir `http://<adresse-du-pi>:5000/data` depuis un appareil du même réseau.
