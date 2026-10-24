import time
import board
import busio
import adafruit_bme280.basic as adafruit_bme280

# Initialisation I2C (GPIO2 = SDA, GPIO3 = SCL)
i2c = busio.I2C(board.SCL, board.SDA)

# Adresse détectée par i2cdetect
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

print("✅ BME280 détecté (Ctrl+C pour arrêter)\n")


try:
    while True:
        print(
            f"T={bme280.temperature:.2f} °C | "
            f"H={bme280.humidity:.2f} % | "
            f"P={bme280.pressure:.2f} hPa"
        )
        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Arrêt utilisateur")

