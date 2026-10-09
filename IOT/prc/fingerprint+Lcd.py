#!/usr/bin/env python3
"""
R307S Fingerprint Attendance/ID Tool
--------------------------------------
All-in-one script:
  1) Enroll a new fingerprint (with a name attached)
  2) Verify a fingerprint -> shows whose finger it is
  3) List everyone enrolled so far
  4) Exit

Names are not stored on the sensor itself (the sensor only stores
fingerprint templates against numeric IDs), so this script keeps a
small local JSON file (fingerprint_names.json) in the same folder,
mapping each ID to a name.

Requirements:
    pip install pyfingerprint --break-system-packages

Wiring (R307S is 3.3V TTL, no level shifter needed):
    Sensor VCC (red)    -> Pi Pin 2  (5V)
    Sensor GND (black)  -> Pi Pin 6  (GND)
    Sensor RX  (white)  -> Pi Pin 8  (GPIO14 / TXD)
    Sensor TX  (yellow) -> Pi Pin 10 (GPIO15 / RXD)

LCD wiring (16x2 with I2C backpack):
    LCD VCC -> Pi Pin 2 (5V)
    LCD GND -> Pi Pin 6 (GND)
    LCD SDA -> Pi Pin 3 (GPIO2 / SDA)
    LCD SCL -> Pi Pin 5 (GPIO3 / SCL)

Extra setup for the LCD (in addition to the fingerprint sensor setup):
    1) sudo raspi-config -> Interface Options -> I2C -> Enable, then reboot
    2) sudo apt install -y i2c-tools
    3) i2cdetect -y 1   (note the address shown, usually 0x27 or 0x3F)
    4) pip install RPLCD smbus2 --break-system-packages
    5) Set LCD_ADDRESS below to match what i2cdetect showed
"""

import sys
import time
import json
import os

try:
    from pyfingerprint.pyfingerprint import PyFingerprint
except ImportError:
    print("pyfingerprint is not installed. Run: pip install pyfingerprint --break-system-packages")
    sys.exit(1)

# ---- Config ----
SERIAL_PORT = '/dev/serial0'   # try '/dev/ttyAMA0' if this doesn't work
BAUD_RATE = 57600
PASSWORD = 0x00000000          # R307S's actual default password

NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fingerprint_names.json')

LCD_ADDRESS = 0x27   # change this to match what i2cdetect -y 1 showed (0x27 or 0x3F are common)


# ---------------- LCD (16x2, I2C) ----------------

lcd = None
try:
    from RPLCD.i2c import CharLCD
    lcd = CharLCD(i2c_expander='PCF8574', address=LCD_ADDRESS, port=1,
                  cols=16, rows=2, charmap='A00', auto_linebreaks=True)
except Exception as e:
    print(f"[WARNING] Could not initialize the LCD: {e}")
    print("The program will still work, just without the display. Check wiring/address/i2cdetect.")
    lcd = None


def lcd_write(line1, line2):
    """Writes two centered lines to the 16x2 LCD. Does nothing if the LCD isn't available."""
    if lcd is None:
        return
    try:
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(line1[:16].center(16))
        lcd.cursor_pos = (1, 0)
        lcd.write_string(line2[:16].center(16))
    except Exception as e:
        print(f"[WARNING] LCD write failed: {e}")


def lcd_show_idle():
    """The default idle screen: 'Fingerprint' on top, 'Checker' centered below."""
    lcd_write("Fingerprint", "Checker")


# ---------------- Name mapping (JSON file) ----------------

def load_names():
    if not os.path.exists(NAMES_FILE):
        return {}
    try:
        with open(NAMES_FILE, 'r') as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError):
        return {}


def save_names(names):
    with open(NAMES_FILE, 'w') as fh:
        json.dump(names, fh, indent=2)


# ---------------- Sensor connection ----------------

def flush_stale_bytes():
    """Clears any leftover bytes sitting in the serial buffer."""
    try:
        import serial
        raw = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(0.3)
        raw.reset_input_buffer()
        raw.reset_output_buffer()
        raw.close()
        time.sleep(0.3)
    except Exception:
        pass


def connect():
    """Connects to the sensor and prints basic info."""
    flush_stale_bytes()

    last_error = None
    for attempt in range(1, 4):
        try:
            f = PyFingerprint(SERIAL_PORT, BAUD_RATE, 0xFFFFFFFF, PASSWORD)
        except Exception as e:
            last_error = f"connect error: {e}"
            time.sleep(0.5)
            continue

        if f.verifyPassword():
            print("[OK] Connected to the module successfully!")
            print(f"  Capacity        : {f.getStorageCapacity()} templates")
            print(f"  Stored templates: {f.getTemplateCount()}")
            return f
        else:
            last_error = "password verification returned false"
            print(f"[RETRY {attempt}/3] Password verification failed, retrying...")
            time.sleep(0.5)

    print(f"[ERROR] Could not connect after 3 attempts. Last reason: {last_error}")
    sys.exit(1)


# ---------------- Enroll ----------------

def enroll(f, names):
    try:
        print("\nPlace your finger on the sensor...")
        while not f.readImage():
            pass
        f.convertImage(0x01)

        result = f.searchTemplate()
        position_number = result[0]
        if position_number >= 0:
            existing_name = names.get(str(position_number), "(name not on record)")
            print(f"[INFO] This finger is already enrolled — {existing_name} (ID #{position_number})")
            return

        name = input("Enter a name for this finger: ").strip()
        if not name:
            print("[ERROR] Name cannot be empty, enrollment cancelled.")
            return

        print("Remove your finger...")
        time.sleep(2)

        print("Place the same finger again...")
        while not f.readImage():
            pass
        f.convertImage(0x02)

        if f.compareCharacteristics() == 0:
            print("[ERROR] The two scans didn't match, try again.")
            return

        f.createTemplate()
        position_number = f.storeTemplate()

        names[str(position_number)] = name
        save_names(names)

        print(f"[OK] Enrolled {name}'s finger! (ID #{position_number})")

    except Exception as e:
        print(f"[ERROR] Enrollment failed: {e}")


# ---------------- Verify ----------------

def verify(f, names):
    try:
        print("\nPlace your finger on the sensor to verify...")
        while not f.readImage():
            pass
        f.convertImage(0x01)

        result = f.searchTemplate()
        position_number, accuracy_score = result

        if position_number == -1:
            print("[NO MATCH] This finger doesn't match any enrolled ID.")
            lcd_write("No match", "Try again")
        else:
            name = names.get(str(position_number), "(name not on record for this ID)")
            print(f"\n>>> Welcome, {name}! <<<")
            print(f"    (ID #{position_number}, confidence score: {accuracy_score})")
            lcd_write("Welcome", name)

        time.sleep(3)
        lcd_show_idle()

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        lcd_show_idle()


# ---------------- List ----------------

def list_enrolled(names):
    if not names:
        print("\nNo one is enrolled yet.")
        return
    print("\n=== Enrolled people ===")
    for id_str, name in sorted(names.items(), key=lambda x: int(x[0])):
        print(f"  ID #{id_str}: {name}")


# ---------------- Main ----------------

def main():
    print("=== R307S Fingerprint Attendance/ID Tool ===\n")
    f = connect()
    names = load_names()
    lcd_show_idle()

    while True:
        print("\nWhat would you like to do?")
        print("  1) Enroll a new fingerprint (with a name)")
        print("  2) Verify a fingerprint (shows the name)")
        print("  3) List all enrolled people")
        print("  4) Exit")
        choice = input("Choice (1-4): ").strip()

        if choice == '1':
            enroll(f, names)
        elif choice == '2':
            verify(f, names)
        elif choice == '3':
            list_enrolled(names)
        elif choice == '4':
            print("Bye!")
            break
        else:
            print("Invalid choice, try again.")


if __name__ == '__main__':
    main()
