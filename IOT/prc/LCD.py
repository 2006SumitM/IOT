from RPLCD.i2c import CharLCD
from time import sleep

lcd = CharLCD('PCF8574', 0x27, cols=16, rows=2)

lcd.clear()
lcd.write_string('Hello SUMIT!')
lcd.cursor_pos = (1, 0)
lcd.write_string('LCD Working')

sleep(10)
lcd.clear()
