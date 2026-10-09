import time
import board
import busio
from adafruit_pn532.i2c import PN532_I2C

i2c = busio.I2C(board.SCL, board.SDA)

pn532 = PN532_I2C(i2c, debug=False)

ic, ver, rev, support = pn532.firmware_version

print("--------------------------------")
print("PN532 NFC Reader")
print("--------------------------------")
print(f"Firmware: {ver}.{rev}")

pn532.SAM_configuration()

print("\nWaiting for NFC card...")
print("Tap your card on the PN532...\n")

last_uid = None

while True:

    uid = pn532.read_passive_target(timeout=0.5)

    if uid is None:
        continue

    uid_string = "".join(f"{byte:02X}" for byte in uid)

    if uid_string != last_uid:
        print("NFC Card Detected!")
        print("UID:", uid_string)
        print("UID Bytes:", [hex(x) for x in uid])
        print("--------------------------------")

        last_uid = uid_string

    time.sleep(0.5)
