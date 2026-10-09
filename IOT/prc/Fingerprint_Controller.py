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
SERIAL_PORT = '/dev/ttyAMA0'   # try '/dev/ttyAMA0' if this doesn't work
BAUD_RATE = 57600
PASSWORD = 0x00000000          # R307S's actual default password

NAMES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fingerprint_names.json')


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
        else:
            name = names.get(str(position_number), "(name not on record for this ID)")
            print(f"\n>>> Welcome, {name}! <<<")
            print(f"    (ID #{position_number}, confidence score: {accuracy_score})")

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")


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