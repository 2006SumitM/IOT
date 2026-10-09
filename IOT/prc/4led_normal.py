import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

led1 = 3
led2 = 7
led3 = 11
led4 = 15

GPIO.setup(led1, GPIO.OUT)
GPIO.setup(led2, GPIO.OUT)
GPIO.setup(led3, GPIO.OUT)
GPIO.setup(led4, GPIO.OUT)

while True:
    GPIO.output(led1, True)
    time.sleep(0.5)
    GPIO.output(led1, False)

    GPIO.output(led2, True)
    time.sleep(0.5)
    GPIO.output(led2, False)

    GPIO.output(led3, True)
    time.sleep(0.5)
    GPIO.output(led3, False)

    GPIO.output(led4, True)
    time.sleep(0.5)
    GPIO.output(led4, False)
