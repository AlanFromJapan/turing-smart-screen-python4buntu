"""
Alan Turing PerfMon LCD display script
--------------------------------------
Ok the pun is under the noose, but this script is to monitor server and my name is Alan, and this is for the Turing smart screens :P
""" 
import datetime
import signal
import os
import time
import traceback
from library.lcd.lcd_comm_rev_a import LcdCommRevA, Orientation

from library.sensors.sensors_snmp import get_snmp, get_snmp_wellknown, initialize_snmp
from library.sensors.sensors_utils import AveragedStack, oneof
from library.sensors.sensors_network import is_port_open_wellknown, is_http_service_available_wellknown, initialize_network

from library.log import logger

import re

# Regex to detect numbers
REX_NUMBER = re.compile(r'^\d+(\.\d+)?$')

# Sleep 5 secs between loops
LOOP_SLEEP_TIME = 5
# Call the real function once every 36 calls ( approx every 3 mins )
ONEOF = 36

stop = False 
def sighandler(signum, frame):
    global stop
    stop = True


def to_float(s: str, default: float) -> float:
    """ Check if the string is a number using regex. """
    if s is None:
        return default
    if isinstance(s, (int, float)):
        return float(s)
    if REX_NUMBER.match(s):
        return float(s)
    return default

# Set the signal handlers, to send a complete frame to the LCD before exit
signal.signal(signal.SIGINT, sighandler)
signal.signal(signal.SIGTERM, sighandler)
is_posix = os.name == 'posix'
if is_posix:
    signal.signal(signal.SIGQUIT, sighandler)

logger.info("Starting Alan Turing PerfMon LCD display script")

# init LCD ( I have a Turing Rev A 3.5" )
lcd=LcdCommRevA() # default is AUTO,320,480
lcd.Reset() # Does nothing for Rev A hardware
lcd.InitializeComm()
lcd.SetOrientation(Orientation.LANDSCAPE)
#set brightness low to avoid heating issues they say on the doc
lcd.SetBrightness(10)

logger.info("Display monitor active, now setting up monitoring loop.")

try:
    current_script_path = os.path.dirname(os.path.abspath(__file__))    

    #initialize SNMP
    if not initialize_snmp(os.path.join(current_script_path, "config/snmp_config.json")):
        logger.error("Failed to initialize SNMP from config.")
        exit(1)
    
    #initialize Network
    if not initialize_network(os.path.join(current_script_path, "config/nw_config.json")):
        logger.error("Failed to initialize Network from config.")
        exit(1)

    # CPU load averaged stack: stack of 20 latest averaged values over 5 inputs
    load_stack = AveragedStack(max_stack_len=20, average_len=5, init_value=0.0)

    # background graphic
    back=os.path.join(current_script_path, 'res/backgrounds/Smoke_480x320.png')
    lcd.DisplayBitmap(back)

    # styles
    font_forecolor = (100,255,100)
    font_forecolor_ERROR = (255,0,0)
    font_bold = os.path.join(current_script_path, "res/fonts/geforce/GeForce-Bold.ttf")
    font_regular = os.path.join(current_script_path, "res/fonts/geforce/GeForce-Light.ttf")
    font_size_title = 24
    font_size_regular = 18


    vert_space_delta = font_size_title +2
    vert_offset = 2
    horiz_offset = 20


    # Love or Hate python...
    def disp(text, x= horiz_offset, good=True):
        global vert_offset
        color = font_forecolor if good else font_forecolor_ERROR
        font = font_regular if good else font_bold
        lcd.DisplayText(text, x, vert_offset, font_size=font_size_regular, font=font, font_color=color, background_image=back)
        vert_offset += vert_space_delta

    logger.info("Entering main monitoring loop.")
    while not stop:
        # ---------------------- LEFT SIDE ----------------------
        vert_offset = 2
        horiz_offset = 20
        lcd.DisplayText("ATLAS", 0, vert_offset, font_size=font_size_title, font=font_bold, font_color=font_forecolor, background_image=back)
        vert_offset += vert_space_delta

        res, val = get_snmp_wellknown(host_nickname="ATLAS", oid_descr="CPU temp miliCelsius (default)")
        disp(f"Temperature: {int(to_float(val, 0))} °C   ", good=res)

        res, val = get_snmp_wellknown(host_nickname="ATLAS", oid_descr="CPU User Percentage")
        disp(f"CPU User %: {int(to_float(val, 0))} %   ", good=res)

        res, val = get_snmp_wellknown(host_nickname="ATLAS", oid_descr="RAID status")
        disp(f"RAID status   ", good=res)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="owncloud")
        disp(f"Owncloud site   ", good=res)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="pihole")
        disp(f"Pihole site   ", good=res)

        # res = is_http_service_available_wellknown(service_name="backup")
        # disp(f"Backup server: {'ok' if res else 'ERROR'}", good=res)

        #empty space
        vert_offset += vert_space_delta

        #Load average graph
        res, val = get_snmp_wellknown(host_nickname="ATLAS", oid_descr="Load average 5min")
        disp(f"Load 5min: {'{:.2f}'.format(to_float(val, 0))}   ", good=res)
        load_stack.add(to_float(val, 0))
        cpu_load, cpu_min, cpu_max = load_stack.stack, load_stack.min(), load_stack.max()

        #empty space
        vert_offset += 6

        # draw CPU load histogram
        lcd.DisplayLineGraph(x=horiz_offset, y=vert_offset, width=200, height=50, values=cpu_load, min_value=cpu_min, max_value=cpu_max, line_color=(0,255,0), background_color=(30,30,30), graph_axis=True, axis_color=(0,255,0), axis_font=font_regular, axis_font_size=14, axis_minmax_format="{:0.2f}")

        # ---------------------- RIGHT SIDE ----------------------
        vert_offset = 2
        horiz_offset = 240
        lcd.DisplayText("SERVICES & URLs", horiz_offset, vert_offset, font_size=font_size_title, font=font_bold, font_color=font_forecolor, background_image=back)
        vert_offset += vert_space_delta

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="electrogeek")
        disp(f"Electrogeek.cc site", good=res, x=horiz_offset)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="ayase-camera")
        disp(f"IPCam Ayase site", good=res, x=horiz_offset)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="oshibi-camera")
        disp(f"IPCam Oshibi site", good=res, x=horiz_offset)

        # ---------------------- BOTTOM SIDE ----------------------
        lcd.DisplayText(f"Updated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 330, 320-16, font_size=12, font=font_regular, font_color=font_forecolor, background_image=back)

        time.sleep(5)
        
except Exception as e:
    logger.error(f"Exception occured: {e}")
    logger.error(traceback.format_exc())

finally:
    lcd.ScreenOff()
    lcd.closeSerial()
    exit(0)