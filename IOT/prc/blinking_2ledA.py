import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BOARD)
led1=3
led2=7
GPIO.setup(led1,GPIO.OUT)
GPIO.setup(led2,GPIO.OUT)
while True:
    GPIO.output(led1,True)
    time.sleep(0.5)
    GPIO.output(led2,True)
    time.sleep(0.5)
    GPIO.output(led2,False)
    time.sleep(0.5)
    GPIO.output(led1,False)
    time.sleep(0.5)
    
