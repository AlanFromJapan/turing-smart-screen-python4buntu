 
import signal
import os
from library.lcd.lcd_comm_rev_a import LcdCommRevA, Orientation

stop = False 
def sighandler(signum, frame):
    global stop
    stop = True

# Set the signal handlers, to send a complete frame to the LCD before exit
signal.signal(signal.SIGINT, sighandler)
signal.signal(signal.SIGTERM, sighandler)
is_posix = os.name == 'posix'
if is_posix:
    signal.signal(signal.SIGQUIT, sighandler)

# init LCD
lcd=LcdCommRevA() # default is AUTO,320,480
lcd.Reset() # Does nothing for Rev A hardware
lcd.InitializeComm()
lcd.SetOrientation(Orientation.LANDSCAPE)
lcd.SetBrightness(10)
 
# background graphic
back='zelda.png'
lcd.DisplayBitmap(back)

"""
To monitor:
- server load
- server CPU temp
- service status
- backup server status (services)

""" 

# put title on LCD
title = "coucou"
print(f"Found {title}\n")
lcd.DisplayText(" " + title, 0, 280, font_size=16, font_color=(0,0,0), background_color=(255,255,255))

val = 0
while not stop:
    lcd.DisplayRadialProgressBar(198, 260, 25, 6,
        min_value=0,
        max_value=100,
        value=val,
        angle_sep=0,
        bar_color=(255, 255, 100),
        font_color=(255, 255, 255),
        background_image=back)

    val = (val + 5) % 100     
    pass
lcd.ScreenOff()
lcd.closeSerial()
exit(0)