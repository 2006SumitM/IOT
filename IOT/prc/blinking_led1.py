import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BOARD)
led=3
GPIO.setup(led,GPIO.OUT)
while True:
    GPIO.output(led,True)
    time.sleep(0.5)
    GPIO.output(led,False)
    time.sleep(1)
