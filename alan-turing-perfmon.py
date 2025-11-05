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

# Sleep 5 secs between loops
LOOP_SLEEP_TIME = 5
# Call the real function once every 36 calls ( approx every 3 mins )
ONEOF = 36

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

# init LCD ( I have a Turing Rev A 3.5" )
lcd=LcdCommRevA() # default is AUTO,320,480
lcd.Reset() # Does nothing for Rev A hardware
lcd.InitializeComm()
lcd.SetOrientation(Orientation.LANDSCAPE)
#set brightness low to avoid heating issues they say on the doc
lcd.SetBrightness(10)
 
try:
    #initialize SNMP
    if not initialize_snmp("config/snmp_config.json"):
        print("Failed to initialize SNMP from config.")
        exit(1)
    
    #initialize Network
    if not initialize_network("config/nw_config.json"):
        print("Failed to initialize Network from config.")
        exit(1)

    # CPU load averaged stack: stack of 20 latest averaged values over 5 inputs
    load_stack = AveragedStack(max_stack_len=20, average_len=5, init_value=0.0)

    # background graphic
    back='res/backgrounds/Smoke_480x320.png'
    lcd.DisplayBitmap(back)

    # styles
    font_forecolor = (100,255,100)
    font_forecolor_ERROR = (255,0,0)
    font_bold = "res/fonts/geforce/GeForce-Bold.ttf"
    font_regular = "res/fonts/geforce/GeForce-Light.ttf"
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

    while not stop:
        # ---------------------- LEFT SIDE ----------------------
        vert_offset = 2
        horiz_offset = 20
        lcd.DisplayText("ATLAS", 0, vert_offset, font_size=font_size_title, font=font_bold, font_color=font_forecolor, background_image=back)
        vert_offset += vert_space_delta

        res, val = get_snmp_wellknown(host_nickname="ATLAS", oid_descr="CPU temp miliCelsius (default)")
        disp(f"Temperature: {int(val) if val else -9999} °C", good=res)

        res, val = get_snmp_wellknown(host_nickname="ATLAS", oid_descr="RAID status")
        disp(f"RAID status: {'ok' if res else 'ERROR'}", good=res)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="owncloud")
        disp(f"Owncloud: {'ok' if res else 'ERROR'}", good=res)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="pihole")
        disp(f"Pihole: {'ok' if res else 'ERROR'}", good=res)

        # res = is_http_service_available_wellknown(service_name="backup")
        # disp(f"Backup server: {'ok' if res else 'ERROR'}", good=res)

        #empty space
        vert_offset += vert_space_delta

        #Load average graph
        res, val = get_snmp_wellknown(host_nickname="ATLAS", oid_descr="Load average 5min")        
        disp(f"Load 5min: {'{:.2f}'.format(float(val)) if res else 'ERROR'}", good=res)
        if res and val is not None:
            load_stack.add(float(val))
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
        disp(f"Electrogeek.cc: {'ok' if res else 'ERROR'}", good=res, x=horiz_offset)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="ayase-camera")
        disp(f"IPCam Ayase: {'ok' if res else 'ERROR'}", good=res, x=horiz_offset)

        res = oneof(is_http_service_available_wellknown, ONEOF, service_name="oshibi-camera")
        disp(f"IPCam Oshibi: {'ok' if res else 'ERROR'}", good=res, x=horiz_offset)

        # ---------------------- BOTTOM SIDE ----------------------
        lcd.DisplayText(f"Updated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 350, 320-12, font_size=10, font=font_regular, font_color=font_forecolor, background_image=back)

        time.sleep(5)
        
except Exception as e:
    print(f"Exception occured: {e}")
    print(traceback.format_exc())

finally:
    lcd.ScreenOff()
    lcd.closeSerial()
    exit(0)