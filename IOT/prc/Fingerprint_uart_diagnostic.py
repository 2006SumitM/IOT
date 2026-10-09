#!/usr/bin/env python3
"""
R307S raw UART diagnostic tool
--------------------------------
pyfingerprint library ko bypass karke seedha serial port pe
'verify password' command bhejta hai aur RAW bytes dikhata hai.

Isse pata chalega:
  - Kuch response aa raha hai ya bilkul nahi (wiring/power issue)
  - Sahi header (EF 01) aa raha hai ya garbage (console conflict / baud mismatch)

Requirements:
    pip install pyserial --break-system-packages
"""

import serial
import time
import sys

PORT = '/dev/serial0'   # agar kaam na kare to '/dev/ttyAMA0' try karo
BAUDS_TO_TRY = [57600, 9600, 19200, 38400, 115200]


def build_verify_password_packet():
    """VerifyPassword command packet banata hai (address FFFFFFFF, password FFFFFFFF)."""
    header = [0xEF, 0x01]
    address = [0xFF, 0xFF, 0xFF, 0xFF]
    pid = 0x01
    instruction = 0x13
    password = [0xFF, 0xFF, 0xFF, 0xFF]

    length_bytes_count = 1 + 4 + 2  # instruction + password + checksum
    length = [(length_bytes_count >> 8) & 0xFF, length_bytes_count & 0xFF]

    checksum_data = [pid] + length + [instruction] + password
    checksum = sum(checksum_data) & 0xFFFF
    checksum_bytes = [(checksum >> 8) & 0xFF, checksum & 0xFF]

    packet = header + address + [pid] + length + [instruction] + password + checksum_bytes
    return bytes(packet)


def hex_dump(data):
    if not data:
        return "(kuch bhi nahi mila — empty response)"
    return ' '.join(f'{b:02X}' for b in data)


def test_baud(port, baud):
    print(f"\n--- Testing baud rate: {baud} ---")
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print(f"[ERROR] Port kholte time fail: {e}")
        return False

    time.sleep(0.5)
    ser.reset_input_buffer()

    packet = build_verify_password_packet()
    print(f"Bhej raha hu : {hex_dump(packet)}")
    ser.write(packet)
    time.sleep(0.3)

    response = ser.read(64)
    print(f"Mila response: {hex_dump(response)}")

    ser.close()

    if len(response) >= 2 and response[0] == 0xEF and response[1] == 0x01:
        print(f"[OK] Sahi header (EF 01) mila is baud rate pe: {baud}")
        return True
    elif len(response) == 0:
        print("[NO RESPONSE] Kuch bhi wapas nahi aaya — wiring ya power check karo.")
        return False
    else:
        print("[GARBAGE] Kuch aaya but header galat hai — console conflict ya baud mismatch ho sakta hai.")
        return False


def reliability_loop(port, baud, rounds=5):
    """Same baud rate ko baar-baar test karke reliability check karta hai."""
    print(f"\n=== Reliability check: {rounds} baar {baud} baud pe test kar raha hu ===")
    ok_count = 0
    for i in range(1, rounds + 1):
        print(f"\n[Round {i}/{rounds}]")
        if test_baud(port, baud):
            ok_count += 1
        time.sleep(1)

    print(f"\n=== Reliability Result: {ok_count}/{rounds} successful ===")
    if ok_count == rounds:
        print("Consistent hai — sensor/wiring/power sab theek hai. Ye software/library ka issue hai.")
    elif ok_count == 0:
        print("Ek baar bhi success nahi hua — hardware/wiring/power issue hai.")
    else:
        print("Kabhi kabhi kaam karta hai, kabhi nahi — loose connection ya marginal power ka signal hai.")


def main():
    print("=== R307S Raw UART Diagnostic ===")
    print(f"Port: {PORT}\n")

    success = False
    working_baud = None
    for baud in BAUDS_TO_TRY:
        if test_baud(PORT, baud):
            success = True
            working_baud = baud
            break

    print("\n=== Result ===")
    if success:
        print("Sensor sahi respond kar raha hai. fingerprint_test.py me yehi baud rate daal do.")
        reliability_loop(PORT, working_baud)
    else:
        print("Kisi bhi baud rate pe sahi header nahi mila. Ye check karo:")
        print("  1. cat /boot/firmware/cmdline.txt me console=serial0 to nahi hai")
        print("  2. TX aur RX wires swap karke dobara try karo")
        print("  3. VCC-GND ke beech multimeter se voltage check karo (4.5V+ hona chahiye)")
        print("  4. /dev/ttyAMA0 try karo PORT variable badal ke")


if __name__ == '__main__':
    main()
