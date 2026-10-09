import time
import board
import busio
import digitalio
from adafruit_pn532.i2c import PN532_I2C

AUTHORIZED_UID = "24499704"

LED_PIN = board.D17

led = digitalio.DigitalInOut(LED_PIN)
led.direction = digitalio.Direction.OUTPUT
led.value = False

i2c = busio.I2C(board.SCL, board.SDA)

pn532 = PN532_I2C(i2c, debug=False)

ic, ver, rev, support = pn532.firmware_version

print("--------------------------------")
print("PN532 Access Control")
print("--------------------------------")
print(f"PN532 Firmware: {ver}.{rev}")

pn532.SAM_configuration()

print("Waiting for NFC card...\n")

led_state = False
last_uid = None

while True:

    uid = pn532.read_passive_target(timeout=0.5)

    if uid is None:
        continue

    uid_string = "".join(f"{byte:02X}" for byte in uid)

    if uid_string == last_uid:
        continue

    last_uid = uid_string

    print("Card detected!")
    print("UID:", uid_string)

    if uid_string == AUTHORIZED_UID:

        print("ACCESS GRANTED")

        led_state = not led_state
        led.value = led_state

        if led_state:
            print("LED: ON")
        else:
            print("LED: OFF")

    else:

        print("ACCESS DENIED")
        print("Unknown card!")

    print("--------------------------------")

    time.sleep(1)

    last_uid = None
