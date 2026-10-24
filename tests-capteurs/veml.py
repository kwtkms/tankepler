import time
import csv
import board
import adafruit_veml7700
from datetime import datetime

# 1. Initialisation du capteur
i2c = board.I2C()
sensor = adafruit_veml7700.VEML7700(i2c)

# Nom du fichier de sortie
FILENAME = "donnees_luminosite.csv"

def auto_adjust(sensor):
    """Ajuste la sensibilité en fonction de la lumière actuelle."""
    try:
        lux = sensor.lux
        if lux > 2000:
            sensor.light_gain = adafruit_veml7700.ALS_GAIN_1_8
            sensor.light_integration_time = adafruit_veml7700.ALS_25MS
        elif lux < 10:
            sensor.light_gain = adafruit_veml7700.ALS_GAIN_2
            sensor.light_integration_time = adafruit_veml7700.ALS_800MS
        else:
            sensor.light_gain = adafruit_veml7700.ALS_GAIN_1
            sensor.light_integration_time = adafruit_veml7700.ALS_100MS
    except Exception:
        pass

print(f"Début de l'enregistrement dans {FILENAME}...")

# Création du fichier et ajout de l'en-tête (Header)
with open(FILENAME, mode='a', newline='') as file:
    writer = csv.writer(file)
    # Si le fichier est vide, on écrit les titres des colonnes
    if file.tell() == 0:
        writer.writerow(["Date et Heure", "Luminosite (Lux)", "Gain", "Temps Integration (ms)"])

try:
    while True:
        # Ajustement de la sensibilité
        auto_adjust(sensor)
        time.sleep(0.2) # Pause technique pour laisser le capteur s'ajuster
        
        # Récupération des données
        maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lux = sensor.lux
        gain = sensor.light_gain
        it_time = sensor.light_integration_time
        
        # Affichage dans le terminal pour vérification
        print(f"[{maintenant}] {lux:.2f} Lux")
        
        # Enregistrement dans le fichier CSV
        with open(FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([maintenant, lux, gain, it_time])
            
        # Pause de 10 secondes (modifiable selon vos besoins)
        time.sleep(10)

except KeyboardInterrupt:
    print("\nEnregistrement terminé.")