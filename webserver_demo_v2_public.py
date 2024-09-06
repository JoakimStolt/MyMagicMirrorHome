import datetime
import RPi.GPIO as GPIO
import time
import threading
import atexit
import feedparser
import io
from flask import Flask, render_template, request 
from flask import Flask, jsonify
import json
import requests
from requests_oauthlib import OAuth1
import urllib.request
import sys
import subprocess
import os
import csv
import pythermiagenesis
import asyncio
import calendar
import pymysql
from huawei_solar import AsyncHuaweiSolar, register_names as rn
from datetime import timedelta
from smbus import SMBus
from DFRobot_DF2301Q import *

#asyncIO
loop = asyncio.get_event_loop()

debug = ""

#MySQL
db = pymysql.connect("localhost","<user>","<psw>","<db>" )
db2 = pymysql.connect("localhost","<user>","<psw>","<db>" )

#Setup Web Server with Flask
IPADDRESS = '192.168.1.221'
IPPORT = 8082
os.chdir('/home/magic/web-server')
JSONIFY_PRETTYPRINT_REGULAR = True

#Voice recognition
DF2301Q = DFRobot_DF2301Q_I2C(i2c_addr=DF2301Q_I2C_ADDR, bus=1)
timerVoice = 0
menu_timer = 0 
menupage = 0

#Thread task polling-times
PIR_PIN = 23
POLL_TIME_ASYNC = 10
POLL_TIME_SH = 10
POLL_TIME_PIR = 0.5
POLL_TIME_LG = 10
POLL_TIME = 600 #Seconds
POLL_TIME_TELL = 30 
POLL_TIME_OCT = 30
POLL_TIME_NEWS = 3600 #Seconds
POLL_TIME_WEATHER = 1800 #Seconds
POLL_TIME_CMD = 30
POLL_TIME_TB = 600
POLL_TIME_HEAT = 10

#Initiate HTTP and IOs
app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
#app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=2)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Initiate Interrupts
dataLock = threading.Lock()
updHusqvarna = threading.Thread()
updTelldus = threading.Thread()
updWeather = threading.Thread()
updNews = threading.Thread()
updCommand = threading.Thread()
updOcto = threading.Thread()
updtc = threading.Thread()
updPir = threading.Thread()
updLg = threading.Thread()
updTB = threading.Thread()
updHeatpump = threading.Thread()
updWater = threading.Thread()

#HTTP Update structures
data2=[]
data3=[]
cmd=""  #Command sent to slave units
display = 1
display_timer = 0
lastDay=0
lastHour=0

pPool = time.time()
pSummer = time.time()
pMeter = time.time()
pMeter2 = time.time()
tPool = None
tSummer = None
tMeter = None
tMeter2 = None
sPool = 0
sSummer = 0
sMeter = 0
sMeter2 = 0

#Electric prices
ELNET_MON = 257.95
ELNET_PRICE = 0.2546
ELNET_TAX = 0.4280
EL_MON = 0.3945
EL_PURCH = 0.021
EL_CERT = 0.0032
EL_ADDON = 0.06
SOLAR_BONUS = 0.02
SOLAR_NET = 0.1046

#Heatpump
HOST = "192.168.1.133"
PORT = 502
tdata = ""
HEAT_HOURS_ON = 11   #Heating wil be on for X hours with lowest price
PRICE_MIN = 1.5
PRICE_MAX = 3
PRICE_OK = 0.8
HEAT_TEMP = 20
class hp:
    outdoor=float(0)
    supply_line=float(0)
    supply_req=float(0)
    return_line=float(0)
    brine_in=float(0)
    brine_out=float(0)
    water=float(0)
    compressor_runtime=float(0)
    water_runtime=float(0)
    heat_runtime=float(0)
    room_temp=float(0)
    mode=""
    modelast=""
    compressor_speed=0
    compressor_precent=float(0)
    high_pressure=float(0)
    low_pressure=float(0)
    condens_pump_speed=float(0)
    brine_pump=""
    circ_pump=""
    condens_pump=""
    compressor=""
    mix_valve_pump=""
    twc_supply_pump=""
    extra_heater=""
    heat_curve=float(0)
    temp_set=21
    temp_set_last=0
    wind_adj=0
    price_adj=0
    lasthour=0
    alarm=0
    alarm_msg=""
    time=0
    timer=0
    time_alert=0      

#Log values 
class logv:
    lasthour=0
    lastday=0
    hour=0
    day=0
    energymeter_lasthour=0
    energy_hour=0
    energymeter_lasthour_prod=0
    energy_hour_prod=0
    solar_lasthour=0
    solar_hour=0
    water_lasthour=0
    water_hour=0
    ch1_hour=0
    ch1_lasthour=0
    ch1_lastId=0
    energymeter2_lasthour=0
    energy2_hour=0
    energymeter2h_lasthour=0
    energy2h_hour=0
    energymeter2w_lasthour=0
    energy2w_hour=0
    c_energymeter_lasthour=0
    c_energy_hour=0
    time=0
    timer=0
    time_alert=0    

#Castle
class castle:
    tempOut=float(0)
    tempUnit=float(0)
    energy=float(0)
    energy_meter=float(0)
    effect_L1=float(0)
    effect_L2=float(0)
    effect_L3=float(0)
    voltage_L1=0
    voltage_L2=0
    voltage_L3=0
    current_L1=float(0)
    current_L2=float(0)
    current_L3=float(0)
    tempIn=float(0)
    humidity=float(0)
    water=0
    temp_water=float(0)
    runtime=0
    time=0
    timer=0

#EnergyMeter
class energyc:
    datetime=0
    energy_meter=0
    energy=float(0)
    energy_meter_prod=0
    energy_prod=float(0)
    effect_L1=float(0)
    effect_L2=float(0)
    effect_L3=float(0)
    phase_voltage=0
    line_voltage=0    
    voltage_L1=0
    voltage_L2=0
    voltage_L3=0
    current_L1=float(0)
    current_L2=float(0)
    current_L3=float(0)
    temp=float(0)
    year_est=float(0)
    year_est_tot=float(0)
    month_est=float(0)
    month=float(0)
    month_est_tot=float(0)
    month_prod=float(0)
    day_est=0
    day_prod=0
    day=0
    day_est_tot=0
    month_est2=0
    day_est2=0
    runtime=0
    time=0
    timer=0
    time_alert=0
    day_arr= [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ]

energymeter = energyc()
energymeter2 = energyc()


#Telldus live
class telldus:
    in_temp=float(0)
    in_hum=0
    out_temp=float(0)
    con_temp=0
    con_hum=0
    pool_pump=0
    pool_cl=0
    time=0
    timer=0
    time_alert=""
#    noService=0

#avgConsumption = [14.0, 11.9, 11.7, 10.7, 8.7, 7.1, 7.5, 7.0, 6.9, 7.3, 8.0, 10.8]
avgConsumption = [11.7, 10.8, 10.1, 8.7, 7.9, 6.2, 6.7, 6.8, 5.6, 6.7, 7.7, 11.1]

#Telldus Access ************************************
Client_id='XXXXXX'
Public_key='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
Private_key='ZUXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
Token='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
Token_secret='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
protected_url = 'https://api.telldus.com/json/'



#Weather
class weather:
    pressure=0
    forecast=0
    rain=0
    rainsw=0
    wind=0
    windmax=0
    beaufort=0
    time=0
    timer=0
    time_alert=""
    forecastDesc=""

#Pool 
class pool:
    temp_sauna=float(0)
    sauna = 0
    sauna_cmd = ""
    temp_in=float(0)
    temp_pool=float(0)
    temp_gh=float(0)
    temp_runtime=0
    ph=float(0)
    orp=float(0)
    level=1
    door=1
    door_last=1
    moisture=float(0)
    fill=0
    filltimer=float(0)
    waittimer=float(0)
    last_fill = ""
    pON = 0
    runtime=0
    time=0
    timer=0
    time_alert=""

#PoolPump
class pump:
    pressure=0
    runtime=0

#Octoprint
octoresp=""
d_state=""
d_percent=0
d_file=""
d_time=0
d_timeleft=0

#Weather access key
API_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

Beaufort_scale={ 
0: 'Calm',
1: 'Light Air',
2: 'Light Breeze',
3: 'Gentle Breeze',
4: 'Moderate Breeze',
5: 'Fresh Breeze',
6: 'Strong Breeze',
7: 'Moderate Gale',
8: 'Fresh Gale',
9: 'Strong Gale',
10: 'Storm',
11: 'Violent Storm',
12: 'Hurricane' }

MOVER_ACTIVITY = {
'UNKNOWN': 'Unknown activity',
'NOT_APPLICABLE': 'Manual start required',
'MOWING': 'Mowing',
'GOING_HOME': 'Going home',
'CHARGING': 'Charging',
'LEAVING': 'Leaving charging station',
'PARKED_IN_CS': 'Parked',
'STOPPED_IN_GARDEN': 'Stopped in Garden'
}

MOVER_STATE= {
'UNKNOWN': 'Unknown state',
'NOT_APPLICABLE': 'Not Applicable',
'PAUSED': 'Mower Paused',
'IN_OPERATION': 'In Operation',
'WAIT_UPDATING': 'Updating',
'WAIT_POWER_UP': 'Power Up',
'RESTRICTED': 'Stopped due to Calendar',
'OFF': 'Turned Off',
'STOPPED': 'Stopped',
'ERROR': 'Error',
'FATAL_ERROR': 'Fatal Error',
'ERROR_AT_POWER_UP': 'Error at Power Up'
}

MOVER_ERROR = {
0: '',
1: 'Outside working area',
2: 'No loop signal',
3: 'Wrong loop signal',
4: 'Loop sensor problem, front',
5: 'Loop sensor problem, rear',
6: 'Loop sensor problem, left',
7: 'Loop sensor problem, right',
8: 'Wrong PIN code',
9: 'Trapped',
10: 'Upside down',
11: 'Low battery',
12: 'Empty battery',
13: 'No drive',
14: 'Mower lifted',
15: 'Lifted',
16: 'Stuck in charging station',
17: 'Charging station blocked',
18: 'Collision sensor problem, rear',
19: 'Collision sensor problem, front',
20: 'Wheel motor blocked, right',
21: 'Wheel motor blocked, left',
22: 'Wheel drive problem, right',
23: 'Wheel drive problem, left',
24: 'Cutting system blocked',
25: 'Cutting system blocked',
26: 'Invalid sub-device combination',
27: 'Settings restored',
28: 'Memory circuit problem',
29: 'Slope too steep',
30: 'Charging system problem',
31: 'STOP button problem',
32: 'Tilt sensor problem',
33: 'Mower tilted',
34: 'Cutting stopped - slope too steep',
35: 'Wheel motor overloaded, right',
36: 'Wheel motor overloaded, left',
37: 'Charging current too high',
38: 'Electronic problem',
39: 'Cutting motor problem',
40: 'Limited cutting height range',
41: 'Unexpected cutting height adj',
42: 'Limited cutting height range',
43: 'Cutting height problem, drive',
44: 'Cutting height problem, curr',
45: 'Cutting height problem, dir',
46: 'Cutting height blocked',
47: 'Cutting height problem',
48: 'No response from charger',
49: 'Ultrasonic problem',
50: 'Guide 1 not found',
51: 'Guide 2 not found',
52: 'Guide 3 not found',
53: 'GPS navigation problem',
54: 'Weak GPS signal',
55: 'Difficult finding home',
56: 'Guide calibration accomplished',
57: 'Guide calibration failed',
58: 'Temporary battery problem',
59: 'Temporary battery problem',
60: 'Temporary battery problem',
61: 'Temporary battery problem',
62: 'Temporary battery problem',
63: 'Temporary battery problem',
64: 'Temporary battery problem',
65: 'Temporary battery problem',
66: 'Battery problem',
67: 'Battery problem',
68: 'Temporary battery problem',
69: 'Alarm! Mower switched off',
70: 'Alarm! Mower stopped',
71: 'Alarm! Mower lifted',
72: 'Alarm! Mower tilted',
73: 'Alarm! Mower in motion',
74: 'Alarm! Outside geofence',
75: 'Connection changed',
76: 'Connection NOT changed',
77: 'Com board not available',
78: 'Slipped - Mower has Slipped.Situation not solved with moving pattern',
79: 'Invalid battery combination - Invalid combination of different battery types.',
80: 'Cutting system imbalance Warning',
81: 'Safety function faulty',
82: 'Wheel motor blocked, rear right',
83: 'Wheel motor blocked, rear left',
84: 'Wheel drive problem, rear right',
85: 'Wheel drive problem, rear left',
86: 'Wheel motor overloaded, rear right',
87: 'Wheel motor overloaded, rear left',
88: 'Angular sensor problem',
89: 'Invalid system configuration',
90: 'No power in charging station'
}


#***********************************************************************        
#********************** Flask Main Webserver ***************************       
#***********************************************************************        
@app.route("/")
def main():
    global data2
    global data3
    global menupage
    global menu_timer

    t = threading.current_thread()
    t.name = "#Main Page"    
    print("->Main Page")
    
    with dataLock:        
        now = datetime.datetime.now()
        left = datetime.datetime.now() + datetime.timedelta(seconds = d_timeleft)
        
        timeString = now.strftime("%H:%M")
        dateString = now.strftime("%d %B, %Y")
        hours = now.hour * 60  + now.minute

        alarm=""
        alarm_set=0
        if sh_workshop.hum != None:
            if  int(sh_workshop.hum) > 72:
                alarm_set=1
                alarm = "Humidity in the Workshop is " + str(sh_workshop.hum) + "%"

        #Forecast
        if weather.forecast != 0:
            if weather.forecast == 1:
                weather.forecastDesc = "Rain"
            else:
                weather.forecastDesc = "Unstable"
        else:
            if weather.pressure > 1020:
                weather.forecastDesc = "High Pressure"
            elif weather.pressure > 1005:
                weather.forecastDesc = "Stable"
            else:
                weather.forecastDesc = "Low Pressure"
      
        #Timeout checks
        husqvarna.time_alert = 0
        telldus.time_alert = 0
        energymeter.time_alert = 0
        energymeter2.time_alert = 0
        logv.time_alert = 0
        castle_time_alert = 0
        weather.time_alert = 0
        pool.time_alert = 0
        hp.time_alert = 0
        Huawei_SUN2000.time_alert = 0
        
        if ( time.time() - husqvarna.timer > 800):
            husqvarna.time_alert = 1
            #Restart Husqvarna if crashed
            # if (husqvarna.run == 1):
            #     polltime = 600
            #     print("Restart Husqvarna")
            #     updHusqvarna = threading.Timer(polltime, Husqvarna, ())
            #     updHusqvarna.start()   
        if ( time.time() - telldus.timer > 600):
            telldus.time_alert = 1            
        if ( time.time() - tb.timer > 1200):
             tb.time_alert = 1 
        if ( time.time() - logv.timer > 600):
             logv.time_alert = 1 
        if (time.time() - castle.timer > 600):
            castle_time_alert = 1
        if (time.time() - weather.timer > 600):
            weather.time_alert = 1
        if (time.time() - pool.timer > 600):
            pool.time_alert = 1
        if (time.time() - energymeter.timer > 600):
            energymeter.time_alert = 1
        if (time.time() - energymeter2.timer > 600):
            energymeter2.time_alert = 1
        if (time.time() - hp.timer > 600):
            hp.time_alert = 1
        if (time.time() - Huawei_SUN2000.timer > 600):
            Huawei_SUN2000.time_alert = 1

        #Heatpump check
        if(hp.alarm == True):
            hpalert = ">>>> BOILER ALERT ! <<<<"
            hpalertMsg = hp.alarm_msg
        else:
            hpalertMsg = ""            
            if(hp.supply_line-hp.return_line > 10):
                hpalert=">>>> Delta High, clear filter <<<<"
            else:
                hpalert=""
        
        #Energy bar
        energy_p1 = (energymeter.month_est - float(energymeter2.month_est)) / energymeter.month_est 
        energy_p2 = float(energymeter2.month_est2) / energymeter.month_est 
        energy_p3 = (float(energymeter2.month_est) - float(energymeter2.month_est2)) / energymeter.month_est 
            
        #Pool check
        if(pool.ph < 7):
            ph_msg = ">>>>> Pool pH Level is Low <<<<<"
            ph_err = 1;
        elif (pool.ph > 8):
            ph_msg = ">>>>> Pool pH level is High <<<<<"
            ph_err = 2;
        else:
            ph_msg = ""
            ph_err = 0;
        
        # Check Pool level
        level_err = ""
        lvl = 0
        if (pool.fill == 1):
            level_err = ">>>>> Filling pool (" + "{:10.0f}".format(pool.filltimer) + "s) <<<<<"
            lvl = 2
            pool.last_fill = now.strftime("%Y-%m-%d %H:%M");
        elif (pool.fill == 2):
            level_err = ">>>>> Filling failure <<<<<"
            lvl = 3
        elif (pool.level == 1):
            level_err = ">>>>> Pool level is Low (" + "{:10.0f}".format(pool.waittimer) + "s) <<<<<"
            lvl = 1       
            
        #Cabin check
        if (castle.tempOut < 1 or castle.tempUnit < 5 or castle.energy > 1000 or (castle.tempIn > 15 and castle.humidity > 75) or castle.tempIn < 7 or castle.water == 1):
            castle_show = 1
        else:
            castle_show = 0
        
        #Start circulation on low tempeartures
        if (hp.outdoor < 0 and pool.pON == 0):
            #setDevice('Pool Pump', '', '1')
            sh_pump.relay='on'
            print("Turn on pool pump due to low temperatures")
            pool.pON = 1
        elif (hp.outdoor > 5):
            pool.pON = 0
        if (pool.pON == 1):
            pool.level = 'Circulation Started due to low temp'

        #Water
        if (float(water.rate) > 0.1):
            wmError = "The Water flow rate is too high " + water.rate
        else:
            wmError = ""
                   
        #Prepare Telldus sensors, Mower and boiler
        data = [{
            'debug': debug,
            'alarm': alarm,
            'alarm_set': alarm_set,
            
            #Husqvarna
            'time': timeString,
            'date': dateString,
            'name': husqvarna.name[0],
            'status': husqvarna.status[0],
            'name2': husqvarna.name[1],
            'status2': husqvarna.status[1],
            'mbat': husqvarna.bat[0],
            'm2bat': husqvarna.bat[1],
            'merror': husqvarna.error[0],
            'm2error': husqvarna.error[1],
            'idev_time': husqvarna.time,
            'idev_time_alert': husqvarna.time_alert,

            #Telldus and Temps
            'con_temp': telldus.con_temp,
            'con_hum': telldus.con_hum,
            'in_temp': "{:10.1f}".format(hp.room_temp),
            'out_temp': "{:10.1f}".format(hp.outdoor),
            'out_tempf': hp.outdoor,
            'telldus_time': telldus.time,
            'telldus_time_alert': telldus.time_alert,
            
            #Energy Meter
            'energy': "{:10.3f}".format(energymeter.energy-energymeter.energy_prod),
            'energyf': energymeter.energy-energymeter.energy_prod,
            'energy_consumed': "{:10.3f}".format(energymeter.energy + (Huawei_SUN2000.energy/1000-energymeter.energy_prod)),
            'energy_meter_prod': "{:10.0f}".format(energymeter.energy_meter_prod/1000),
            'energyH': "{:10.3f}".format(energymeter.energy - (energymeter2.energy/1000) ),
            'energy_meter': energymeter.energy_meter,      
            'energy_month_prod': "{:10.0f}".format(energymeter.month_prod/1000),
            'energy_day_net': "{:10.0f}".format(energymeter.day_est_net),
            'energy_year': "{:10.0f}".format(energymeter.year_est),
            'energy_month': "{:10.0f}".format(energymeter.month_est),
            'energy_day': "{:10.1f}".format(energymeter.day_est),
            'castle_month': "{:10.0f}".format(energymeter.month_est2),
            'castle_day': "{:10.1f}".format(energymeter.day_est2),
            'energy_p1': energy_p1,
            'energy_p2': energy_p2,
            'energy_p3': energy_p3,
            'energy_time': energymeter.time,
            'energy_time_alert': energymeter.time_alert,

            #Heat pump data
            'hp_energy': "{:10.3f}".format(energymeter2.energy/1000),    
            'hp_outdoor': "{:10.1f}".format(hp.outdoor),
            'hp_indoor': "{:10.1f}".format(hp.room_temp),
            'hp_status': hp.mode,
            'hp_return': "{:10.1f}".format(hp.return_line),
            'hp_supply': "{:10.1f}".format(hp.supply_line),
            'hp_supply_req': "{:10.1f}".format(hp.supply_req),
            'hp_brine_in': "{:10.1f}".format(hp.brine_in),
            'hp_brine_out': "{:10.1f}".format(hp.brine_out),
            'hp_water': "{:10.1f}".format(hp.water),
            'hp_comp_hours': hp.compressor_runtime,
            'hp_water_hours': hp.water_runtime,
            'hp_heat_hours': hp.heat_runtime,
            'hp_comp_speed': hp.compressor_speed,
            'hp_comp_percent': "{:10.0f}".format(hp.compressor_precent),
#            'hp_heat_on': hp.heat_on,
            'hp_adj': hp.wind_adj + hp.price_adj,
            'hp_temp_set': hp.temp_set,
            'hpalarm': hpalert,
            'hpalert': hpalertMsg,
            'delta1': "{:10.1f}".format(hp.supply_line-hp.return_line),
            'delta2': "{:10.1f}".format(hp.brine_in-hp.brine_out),
            'hp_time': hp.time,
            'hp_time_alert': hp.time_alert,
            'energy2_time': energymeter2.time,
            'energy2_time_alert': energymeter2.time_alert,            

            #Water
            'wm_rate': water.rate,
            'wm_value': water.value,
            'wm_error': wmError,

            #Charge Amp
            'ca_status': charger1.status,
            'ca_consumption': "{:10.1f}".format(charger1.totalConsumptionKwh/1000),            
            'Month_Consumption': "{:10.1f}".format(charger1.month_consumption / 1000),
            'Month_Cost': "{:10.0f}".format(charger1.month_cost).strip(),
            
            #Castle
            'sh_temp_out': "{:10.1f}".format(castle.tempOut),
            'sh_temp_unit': "{:10.1f}".format(castle.tempUnit),
            'sh_energy': "{:10.3f}".format(castle.energy),
            'sh_energyf': castle.energy,
            'sh_energy_tot': "{:10.1f}".format(castle.energy_meter),
            'sh_temp_in': "{:10.1f}".format(castle.tempIn),
            'sh_humidity': "{:10.0f}".format(castle.humidity),
            'sh_water': castle.water,
            'sh_temp_water': "{:10.0f}".format(castle.temp_water),
            'sh_show': castle_show,
            'sh_runtime': castle.runtime,
            'sh_time': castle.time,
            'sh_time_alert': castle_time_alert,

            #Solar
            'solar_energy': "{:10.3f}".format(Huawei_SUN2000.energy/1000),
            'solar_energyf': Huawei_SUN2000.energy,
            'solar_status': Huawei_SUN2000.device_status,
            'solar_daily': "{:10.0f}".format(Huawei_SUN2000.daily_yield),
            'solar_monthly': "{:10.0f}".format(Huawei_SUN2000.monthly_yield/1000),
            'solar_monthly_earned': "{:10.0f}".format(Huawei_SUN2000.monthly_payed-Huawei_SUN2000.monthly_earned).strip(),
            'solar_monthly_payed_net': "{:10.0f}".format(Huawei_SUN2000.monthly_payed_net).strip(),
            'solar_monthly_earnedf': Huawei_SUN2000.monthly_payed-Huawei_SUN2000.monthly_earned,
            'solar_acc': "{:10.0f}".format(Huawei_SUN2000.acc_yield/1000),
            'solar_yearly': "{:10.0f}".format(Huawei_SUN2000.yearly_yield/1000),
            'solar_time': Huawei_SUN2000.time,
            'solar_time_alert': Huawei_SUN2000.time_alert,
            
            #Tibber
            't_price': "{:10.2f}".format(tb.price + ((ELNET_PRICE + ELNET_TAX) * 1.25)),
            't_netprice': tb.netprice,
            't_price_break': "{:10.2f}".format(tb.price_break),
            't_pricef': tb.price,
            'logv_time': logv.time,
            'logv_time_alert': logv.time_alert,
            't_time': tb.time,
            't_time_alert': tb.time_alert,
            't_price_today': tb.price_list_today,            
            
            #Weather
            'w_pressure': "{:10.0f}".format(weather.pressure),
            'w_forecast': weather.forecast,
            'w_forecastdesc': weather.forecastDesc,
            'w_rain': weather.rain,
            'w_rainsw': weather.rainsw,
            'w_wind': "{:10.1f}".format(weather.wind),        
            'w_iwind': weather.wind,        
            'w_windmax': "{:10.1f}".format(weather.windmax),        
            'w_beaufort': weather.beaufort,
            'w_beaufortDesc': Beaufort_scale.get(weather.beaufort),
            
            #3D printer
            '3d_state': d_state,
            '3d_percent': "{:10.1f}".format(d_percent),
            '3d_file': d_file,
            '3d_time': "{:02.0f}:{:02.0f}".format(d_time//3600, (d_time%3600)/60),
            '3d_timeleft': "{:02.0f}:{:02.0f}".format(d_timeleft//3600, (d_timeleft%3600)/60),
            '3d_timedone': left.strftime("%H:%M"),
        
            #Pool data
            'temp_sauna': "{:10.1f}".format(pool.temp_sauna),
            'temp_saunaf': pool.temp_sauna,
            'temp_pool': "{:10.1f}".format(pool.temp_pool),
            'temp_poolf': pool.temp_pool,           
            'temp_runtime': pool.temp_runtime,
            'ph': "{:10.1f}".format(pool.ph),
            'ph_err': ph_err,
            'orp': "{:10.0f}".format(pool.orp),
            'orpval': pool.orp,
            'level': pool.level,
            'last_fill': pool.last_fill,
            'door': pool.door,
            'pool_lvl': lvl,
            'level_err': level_err,
            'phmsg': ph_msg,
            'moisture': pool.moisture,
            'pool_runtime': pool.runtime,
            #'pool_pump': telldus.pool_pump,
            'pool_pump': sh_pump.relay,
            'pool_pump_kw': "{:10.3f}".format(sh_pump.kw/1000),
            'pool_cl': sh_clorinator.relay,
            'pool_cl_kw': "{:10.3f}".format(sh_clorinator.kw/1000),
            'sauna' : pool.sauna,
            'sauna_cmd': pool.sauna_cmd,
            'pool_time': pool.time,
            'pool_time_alert': pool.time_alert
            
            }]

        if menupage == 1:
            if time.time() - menu_timer > 60:
                menupage = 0
            return render_template('energy_v1.html', data=data, energy=energymeter.day_arr, solar=Huawei_SUN2000.day_arr, price=tb.price_list_today_unsorted)
        else:
            menu_timer = time.time() 
            return render_template('main_mini_v2.html', data=data, weather=data2, news=data3)


@app.route("/index")
def index():
        t = threading.current_thread()
        t.name = "#Index"    
        print("->Index")

        now = datetime.datetime.now()
        hours = now.hour * 60  + now.minute
           
        #Prepare Telldus sensors, Mower and boiler
        data = [{
            'Husqvarna': {
            #Mower data
            'mname': husqvarna.name[0],
            'mstatus': husqvarna.status[0],
            'merror': husqvarna.error[0],
            'mbat': husqvarna.bat[0],
            'm2name': husqvarna.name[1],
            'm2status': husqvarna.status[1],
            'm2bat': husqvarna.bat[1],
            'm2error': husqvarna.error[1],
            'idev_time': husqvarna.time,
            'idev_time_alert': husqvarna.time_alert },

            'Shelly': {
            'pool_pump': sh_pump.relay,
            'pool_pump_kw': sh_pump.kw,                
            'pool_pump_temp': sh_pump.temp,            
            'clorinator': sh_clorinator.relay,
            'clorinator_kw': sh_clorinator.kw,                
            'clorinator_temp': sh_clorinator.temp,
            'workshop_temp': sh_workshop.temp,
            'workshop_hum': sh_workshop.hum,
            'workshop_bat': sh_workshop.bat,
            'workshop_time': sh_workshop.time,
            'workshop_timer': time.time() - sh_workshop.timer
              },            

            'Solar': {
            'solar_energy': Huawei_SUN2000.energy,
            'solar_device_status': Huawei_SUN2000.device_status,
            'solar_temp': Huawei_SUN2000.temp,
            'solar_daily_yield': Huawei_SUN2000.daily_yield,
            'solar_acc_yield': Huawei_SUN2000.acc_yield,
            'solar_pv1_v': Huawei_SUN2000.pv1_v,
            'solar_pv1_a': Huawei_SUN2000.pv1_a,
            'solar_pv2_v': Huawei_SUN2000.pv2_v,
            'solar_pv2_a': Huawei_SUN2000.pv2_a,
            'solar_input_power': Huawei_SUN2000.input_power,
            'solar_daily_power_peak': Huawei_SUN2000.daily_power_peak,
            'solar_fault_code': Huawei_SUN2000.fault_code,
            'solar_monthly_yield': Huawei_SUN2000.monthly_yield,
            'solar_monthly_earned': Huawei_SUN2000.monthly_earned,
            'solar_monthly_payed': Huawei_SUN2000.monthly_payed,
            'energy_monthly_consumed': energymeter.month,
            'energy_monthly_prod': energymeter.month_prod,            
            'energy_monthly_consumed_avg': Huawei_SUN2000.monthly_earned / energymeter.month * 1000,
            'energy_monthly_prod_avg': Huawei_SUN2000.monthly_payed / energymeter.month_prod * 1000,            
            'solar_yearly_yield': Huawei_SUN2000.yearly_yield,
            'solar_time': Huawei_SUN2000.time,
            'solar_time_alert': Huawei_SUN2000.time_alert    
            },

            'Telldus': {
            #Telldus data
            'con_temp': telldus.con_temp,
            'con_hum': telldus.con_hum,
            #'pool_pump': telldus.pool_pump,
            'pool_cl': telldus.pool_cl,
            'Workshop_temp': telldus.in_temp,
            'Workshop_hum': telldus.in_hum,
            #'out_temp': telldus.out_temp,
            'time': telldus.time,
            'time_alert': telldus.time_alert },
                    
            #Heat pump data
            'HeatPump': {          
            'hp_outdoor': hp.outdoor,
            'hp_mode': hp.mode,
            'hp_return': hp.return_line,
            'hp_supply': hp.supply_line,
            'hp_brine_in': hp.brine_in,
            'hp_brine_out': hp.brine_out,
            'hp_water': hp.water,
            'hp_indoor': "{:10.1f}".format(hp.room_temp),            
            'hp_comp_hours': hp.compressor_runtime,
            #'hp_comp_hours_lsb': hp.compressor_runtime_lsb,
            'hp_water_hours': hp.water_runtime,
            'hp_heat_hours': hp.heat_runtime,
            'hp_comp_speed': hp.compressor_speed,
            'hp_comp_percent': hp.compressor_precent,
            'hp_low_pressure': hp.low_pressure,
            'hp_high_pressure': hp.high_pressure, 
            'hp_supply_req': hp.supply_req,
            'hp_condens_pump_speed': hp.condens_pump_speed,
            'hp_brine_pump': hp.brine_pump,
            'hp_circ_pump': hp.circ_pump,
            'hp_condens_pump': hp.condens_pump,
            'hp_compressor': hp.compressor,
            'hp_smix_valve_pump': hp.mix_valve_pump,
            'hp_twc_supply_pump': hp.twc_supply_pump,
            'hp_extra_heater': hp.extra_heater,
            'hp_heat_curve': hp.heat_curve,
            #'hp_heat_on': hp.heat_on,
            'hp_temp_set': hp.temp_set,
            'hp_wind_adj': hp.wind_adj,
            'hp_price_adj': hp.price_adj,
            'hp_alarm': hp.alarm,
            'hp_alarm_msg': hp.alarm_msg,
            'hp_time': hp.time,
            'hp_time_alert': hp.time_alert },
          
            #EnergyMeter
            'EnergyMeter': {
            't_price': tb.price,
            't_netprice': tb.netprice,
            't_price_today': tb.price_list_today,            
            't_price_break': "{:10.2f}".format(tb.price_break),
            'datetime': energymeter.datetime,
            'energy_meter': energymeter.energy_meter,
            'energy': energymeter.energy,
            'energy_day_net': "{:10.0f}".format(energymeter.day_est_net),
            'energy_meter_prod': energymeter.energy_meter_prod,
            'energy_prod': energymeter.energy_prod,
            'energy_month_consum': energymeter.month,
            'energy_month_prod': energymeter.month_prod,
            'effect_L1': energymeter.effect_L1,
            'effect_L2': energymeter.effect_L2,
            'effect_L3': energymeter.effect_L3,
            'voltage_L1': energymeter.voltage_L1,
            'voltage_L2': energymeter.voltage_L2,
            'voltage_L3': energymeter.voltage_L3,
            'current_L1': energymeter.current_L1,
            'current_L2': energymeter.current_L2,
            'current_L3': energymeter.current_L3,
            'temp': energymeter.temp,
            'month_est': energymeter.month_est,
            'day_est_tot': energymeter.day_est_tot,
            'day_prod': energymeter.day_prod,
            'month_est_tot': energymeter.month_est_tot,
            'day_est': energymeter.day_est,
            'time': energymeter.time,
            'runtime': energymeter.runtime,
            'time_alert': energymeter.time_alert },
                    
            #EnergyMeter 2
            'EnergyMeter2': {
            'energy_meter': energymeter2.energy_meter,
            'energy': energymeter2.energy,
            'effect_L1': energymeter2.effect_L1,
            'effect_L2': energymeter2.effect_L2,
            'effect_L3': energymeter2.effect_L3,
            'phase_voltage': energymeter2.phase_voltage,
            'line_voltage': energymeter2.line_voltage,
            'voltage_L1': energymeter2.voltage_L1,
            'voltage_L2': energymeter2.voltage_L2,
            'voltage_L3': energymeter2.voltage_L3,
            'current_L1': energymeter2.current_L1,
            'current_L2': energymeter2.current_L2,
            'current_L3': energymeter2.current_L3,
            'temp': energymeter2.temp,
            'month_est': energymeter2.month_est,
            'day_est': energymeter2.day_est,
            'heat_month_est': energymeter2.month_est2,
            'heat_day_est': energymeter2.day_est2,
            'time': energymeter2.time,
            'time_alert': energymeter2.time_alert,            
            'runtime': energymeter2.runtime },
            
            #Castle house
            'Castle': {
            'temp_out': castle.tempOut,
            'temp_unit': castle.tempUnit,
            'energy': castle.energy,
            'energy_tot': castle.energy_meter,
            'temp_in': castle.tempIn,
            'humidity': castle.humidity,
            'water': castle.water,
            'temp_water': castle.temp_water,
            'castle_month_est': energymeter.month_est2,
            'castle_day_est': energymeter.day_est2,
            'time': castle.time,
            'runtime': castle.runtime},
                    
            #Water meter
            'Water': {
            'value': water.value,
            'raw value': water.raw,
            'previous': water.pre,
            'error': water.error,
            'rate': water.rate,
            'timestamp': water.timestamp    
            },

            #Charge Amps
            'ChargeAmp': {
            'status': charger1.status,
            'consumption': charger1.totalConsumptionKwh,
            'Month_Consumption': charger1.month_consumption / 1000,
            'Month_Cost': charger1.month_cost
            },

            #Weather
            'Weather': {
            'w_pressure': weather.pressure,
            'w_forecast': weather.forecast,
            'w_forecastdesc': weather.forecastDesc,
            'w_rain': weather.rain,
            'w_rainsw': weather.rainsw,
            'w_wind': weather.wind,
            'w_windmax': weather.windmax,
            'w_beaufort': weather.beaufort,
            'w_beaufortDesc': Beaufort_scale.get(weather.beaufort) },
        
            #Pool data
            'Pool': {
            'temp_sauna': pool.temp_sauna,
            'temp_pool': pool.temp_pool,
            'runtime': pool.runtime,
            'ph': pool.ph,
            'orp': pool.orp,
            'last_fill': pool.last_fill,
            'door': pool.door,
            'moisture': pool.moisture,
            'pool_time': pool.time,
            'pool_runtime': pool.runtime,
            'pool_pump': sh_pump.relay,
            'pool_cl': telldus.pool_cl,
            'sauna_cmd': pool.sauna_cmd,
            'sauna' : pool.sauna },

            #PoolPump data
            'PoolPump': {
            'pump_pressure': pump.pressure,
            'pump_runtime': pump.runtime },

            #Octoprint
            'Octoprint': {
            '3d_state': d_state,
            '3d_percent': d_percent,
            '3d_file': d_file,
            '3d_time': d_time,
            '3d_timeleft': d_timeleft }
            }]
        
        print("->Main done")

        return (jsonify(data + data2 + [data3]))
            
@app.route("/cmd", methods = ['GET'])
def cmdExecute():
    global menupage

    if request.args.get('command') == 'm1':
        menupage = 1
    elif request.args.get('command') == 'm0':
        menupage = 0
    elif request.args.get('command') == 's1':
        pool.sauna_cmd = "1"
    elif request.args.get('command') == 's0':
        pool.sauna_cmd = "2"
    
    return('<200 OK>')
    

#Update Summer house data       
@app.route("/summer", methods = ['POST'])
def summer_post():
    global tSummer
    global pSummer
    global sSummer
    tSummer = threading.current_thread()
    tSummer.name = "#Slottet"    
    print("->Slottet")

    try:
        sSummer = 1
        pSummer= time.time()
        if request.method=="POST":
            content = request.json

            castle.tempOut = content['tempout']
            castle.tempUnit = content['tempunit']
            castle.energy = content['energy']
            castle.energy_meter = content['energy_tot']
            castle.effect_L1 = content['effect_L1']
            castle.effect_L2 = content['effect_L2']
            castle.effect_L3 = content['effect_L3']
            castle.voltage_L1 = content['voltage_L1']
            castle.voltage_L2 = content['voltage_L2']
            castle.voltage_L3 = content['voltage_L3']
            castle.current_L1 = content['current_L1']
            castle.current_L2 = content['current_L2']
            castle.current_L3 = content['current_L3']
          
            castle.tempIn = content['tempin']
            castle.humidity = content['humidity']
            castle.water = content['water']
            castle.temp_water = content['tempwater']
            castle.runtime = content['runtime']
            castle.time = datetime.datetime.now().strftime("%H:%M")
            castle.timer = time.time()

        sSummer = 0
        tSummer = None

        return('Upload OK')
    
    except:
        print("Slottet failed to upload")
        return('Upload Failed')    
    
# #Charge Amps Callback
# @app.route("/chargepoints/2920586C/heartbeat", methods=['POST'])
# def ch_heartbeat():
#     try:
#         print(request.json)
#     except:
#         print("Hearbeat failed")
#     return("200 - Ok")
#         
# @app.route("/chargepoints/2920586C/metervalue", methods=['POST'])
# def ch_metervalue():
#     try:
#         print(request.json)
#     except:
#         print("Metervalue failed")
#     return("200 - Ok")
# 
# @app.route("/chargepoints/2920586C/connectors/1/start", methods=['POST'])
# def ch_start():
#     try:
#         print(request.json)
#     except:
#         print("Start failed")
#     return("200 - Ok")
# 
# @app.route("/chargepoints/2920586C/connectors/1/stop", methods=['POST'])
# def ch_stop():
#     try:
#         print(request.json)
#     except:
#         print("Stop failed")
#     return("200 - Ok")
# 
# @app.route("/chargepoints/2920586C/boot", methods=['POST'])
# def ch_boot():
#     try:
#         print(request.json)
#     except:
#         print("Boot failed")
#     return("200 - Ok")
# 

#Shelly Sensors call-back
@app.route("/shelly", methods=['GET'])
def sh_sensors():
    try:
        
        sh_workshop.temp = float(request.args.get('temp'))
        sh_workshop.hum = int(request.args.get('hum'))
        resp2 = requests.get(url=sh_workshop.ip+'/status', timeout=15).json()
        #print(resp2)
        sh_workshop.bat = resp2['bat']['value']        

        sh_workshop.time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sh_workshop.timer = time.time() 
    except:
        print("Shelly Hearbeat failed")
    return("200 - Ok")

#Update Energy Meter
@app.route("/energymeter", methods = ['POST'])
def energyMeter():
    global tMeter
    global pMeter
    global sMeter
    tMeter= threading.current_thread()
    tMeter.name = "#EnergyMeter"    
    print("->EnergyMeter")

    try:
        sMeter = 1
        pMeter = time.time()    
        if request.method=="POST":
            content = request.json

            #energymeter.datetime = content['datetime']
            #energymeter.energy1_meter = content['energy1_meter']
            #energymeter.energy2_meter = content['energy2_meter']
            #energymeter.energy3_meter = content['energy3_meter']
            #energymeter.energy123_meter = content['energy123_meter']
            #energymeter.energy1 = content['energy1']
            #energymeter.energy2 = content['energy2']
            #energymeter.energy3 = content['energy3']
            #energymeter.energy123 = content['energy123']
            energymeter.energy_meter = content['energy_meter']
            energymeter.energy = content['energy']
            energymeter.energy_meter_prod = content['energy_meter_prod']
            energymeter.energy_prod = content['energy_prod']
            #energymeter.energy_prod = 4000 / 1000
            energymeter.effect_L1 = content['effect_L1']
            energymeter.effect_L2 = content['effect_L2']
            energymeter.effect_L3 = content['effect_L3']
            energymeter.voltage_L1 = content['voltage_L1']
            energymeter.voltage_L2 = content['voltage_L2']
            energymeter.voltage_L3 = content['voltage_L3']
            energymeter.current_L1 = content['current_L1']
            energymeter.current_L2 = content['current_L2']
            energymeter.current_L3 = content['current_L3']
            energymeter.temp = content['temp']

            energymeter.runtime = content['runtime']
            energymeter.time = datetime.datetime.now().strftime("%H:%M")
            energymeter.timer = time.time()
        
        sMeter = 0
        tMeter = None
        
        return('Upload OK')
    
    except:
        print("Energymeter failed to upload")

#Update Energy Meter 2
@app.route("/energymeter2", methods = ['POST'])
def energyMeter2():
    global tMeter2
    global pMeter2
    global sMeter2
    tMeter2 = threading.current_thread()
    tMeter2.name = "#EnergyMeter2"    
    print("->EnergyMeter2")

    try:
        sMeter2 = 1
        pMeter2 = time.time()   
        if request.method=="POST":
            content = request.json

            energymeter2.energy_meter = content['energy_meter']
            energymeter2.energy = content['energy']
            energymeter2.effect_L1 = content['effect_L1']
            energymeter2.effect_L2 = content['effect_L2']
            energymeter2.effect_L3 = content['effect_L3']
            energymeter2.phase_voltage = content['phase_voltage']
            energymeter2.line_voltage = content['line_voltage']
            energymeter2.voltage_L1 = content['voltage_L1']
            energymeter2.voltage_L2 = content['voltage_L2']
            energymeter2.voltage_L3 = content['voltage_L3']
            energymeter2.current_L1 = content['current_L1']
            energymeter2.current_L2 = content['current_L2']
            energymeter2.current_L3 = content['current_L3']
            energymeter2.temp = content['temp']

            energymeter2.runtime = content['runtime']
            energymeter2.time = datetime.datetime.now().strftime("%H:%M")
            energymeter2.timer = time.time()
        
        sMeter2 = 0
        tMeter2 = None

        return('Upload OK')
    
    except:
        print("Energymeter2 failed to upload")

#Update Boiler data by external upload        
@app.route("/clock", methods = ['GET'])
def clock():
    t = threading.current_thread()
    t.name = "#Clock"    

    now = datetime.datetime.now()
    left = datetime.datetime.now() + datetime.timedelta(seconds = d_timeleft)
    
    if husqvarna.status[0] == "Error" or husqvarna.status[0] == "Disabled" or husqvarna.status[0] == "Disconnected":
        malarm = 1
    else:
        malarm = 0
    if husqvarna.status[1] == "Error" or husqvarna.status[1] == "Disabled" or husqvarna.status[1] == "Disconnected":
        m2alarm = 1
    else:
        m2alarm = 0

    if hp.alarm == True:
        hpalarm = 1
        hpalert = hp.alarm_msg
    else:
        hpalarm = 0
        hpalert = ""


    content = jsonify(
        energy=energymeter.energy,
        tempPool=pool.temp_pool,
        temp=hp.outdoor,
        temp_sauna=pool.temp_sauna,
        fill=pool.fill,
        hpalarm=hpalarm,
        hpalert=hpalert,
        wind=weather.wind,
        windmax=weather.windmax,
        beaufort=Beaufort_scale.get(weather.beaufort),
        progress=d_percent,
        timedone=left.strftime("%H:%M")
    )
    
    return content 

# @app.route("/control", methods = ['GET'])
# def controlPanel():
    
#     kitchen = GetDevice('Kitchen', '', 'statevalue')
#     spots = GetDevice('Spots', '', 'statevalue')
#     content = jsonify( 
#         kitchen=kitchen,
#         spots=spots
#     )
    
#     return content 

#Update Pool data by external upload        
@app.route("/pool", methods = ['POST'])
def pool_post():
    global tPool
    global pPool
    global sPool
    tPool= threading.current_thread()
    tPool.name = "#Pool"    
    print("->Pool")
    
    try:
        sPool = 1
        pPool= time.time()   
        if request.method=="POST":
            content = request.json
    
            pool.temp_pool = content['temp1'] 
            pool.temp_sauna = content['temp2']
            pool.ph = content['ph']
            pool.orp = content['orp']
            pool.level = content['level']
            pool.door = content['door']
            pool.fill = content['filling']
            pool.waittimer = content['waittimer'] / 1000
            pool.filltimer = content['filltimer'] / 1000
            pool.moisture = content['moisture']
            pool.runtime = content['runtime']
            pool.sauna = content['sauna']
            weather.pressure = content['pressure']
            weather.forecast = content['forecast']
            weather.rain = content['rain']
            weather.rainsw = content['rainsw']
            weather.wind = content['wind']
            weather.windmax = content['windmax']
            weather.beaufort = content['beaufort']
        
            pool.time = datetime.datetime.now().strftime("%H:%M")
            pool.timer = time.time()
       
        return_cmd = jsonify(command=pool.sauna_cmd)
        pool.sauna_cmd = ""

        sPool = 0
        tPool = None

        return return_cmd

    except:
        print("Pool failed to upload")            
        

#Update Pool data by external upload        
@app.route("/poolpump", methods = ['POST'])
def pump_post():
    
    try:
        if request.method=="POST":
            content = request.json
    
            pump.pressure = content['pressure'] 
            pump.runtime = content['runtime']
        
            pumptime = datetime.datetime.now().strftime("%H:%M")
            pump.timer = time.time()

        return('Upload OK')

    except:
        print("Pool Pump failed to upload")            
        
        
#***************************************** Tibber ***************************************************        
class tibber:
    url=""
    token=""
    request=""
    location=0
    price=0
    netprice=0
    price_lvl=0
    nextprice=0
    price_avg=0
    price_list_today = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    price_list_today_unsorted = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    time=""
    price_break=0
    timer=""
    time_alert = 0

    def update(self):
        while True:
            print("Poll Tibber")
            
            self.time = datetime.datetime.now().strftime("%H:%M")
            self.timer = time.time()                
            now = datetime.datetime.now()
            hour = now.hour

  #          if threading.active_count() > 12:
   #             for thread in threading.enumerate(): 
    #                print(thread.name)

            try:
                with dataLock:
                    response = requests.post(self.url,
                                        headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'},
                                        json=self.request, timeout=10).json()
                    
                    self.price = response['data']['viewer']['homes'][self.location]['currentSubscription']['priceInfo']['today'][hour]['total']
                    self.netprice = response['data']['viewer']['homes'][self.location]['currentSubscription']['priceInfo']['today'][hour]['energy']
                    if hour<23:
                        self.nextprice = response['data']['viewer']['homes'][self.location]['currentSubscription']['priceInfo']['today'][hour+1]['total']
                    else:
                        self.nextprice = response['data']['viewer']['homes'][self.location]['currentSubscription']['priceInfo']['tomorrow'][0]['total']
                        
                    self.price_avg = 0
                    for x in range(24):
                        self.price_list_today[x] = response['data']['viewer']['homes'][self.location]['currentSubscription']['priceInfo']['today'][x]['total']
                        self.price_list_today_unsorted[x] = response['data']['viewer']['homes'][self.location]['currentSubscription']['priceInfo']['today'][x]['total']
                        self.price_avg = self.price_avg + response['data']['viewer']['homes'][self.location]['currentSubscription']['priceInfo']['today'][x]['total']
                    self.price_list_today.sort()
                    self.price_break = self.price_list_today[HEAT_HOURS_ON] 
                    self.price_avg = self.price_avg / 24

                    # print(self.price_avg)    
                    # print(self.price_list_today)             
                    # print(response)
                    print("TIBBER")
                    print(self.price)
                    print(self.netprice)
                        
            except:
                print('Failed to access Tibber')
                #print(response)
                
            time.sleep(POLL_TIME_TB)
            

#********************************************** Husqvarna *****************************************************
def controlMower():
    global updCommand
    # global door
    # global door_last
    # global doorCnt
               
    try:
        with dataLock:
            if pool.door == 0 and pool.door_last == 1 and (husqvarna.status[0] == 'Cutting'):
                if pool.doorCnt >= 120 :
                    mwresponse = requests.post(hqurl + '171609690-172030664/control',
                                headers={'Authorization': 'Bearer ' + id_, 'Authorization-Provider': 'husqvarna', 'Content-Type': 'application/json'},
                                json={ "action": "STOP" }, timeout=10).json()
                    pool.door_last = door
                else:
                    pool.doorCnt += 1
            else:
                pool.doorCnt = 0
           
            if pool.door == 1 and pool.door_last == 1 and husqvarna.status[0] == 'Paused':
                mwresponse = requests.post(hqurl + '171609690-172030664/control',
                                headers={'Authorization': 'Bearer ' + id_, 'Authorization-Provider': 'husqvarna', 'Content-Type': 'application/json'},
                                json={ "action": "START" }, timeout=10).json()
                pool.door_last = door
                           
    except:
        print("Husqvarna Control Task Failed")

    print("Initiate Husvarna Control")
    updCommand = threading.Timer(POLL_TIME_CMD, controlMower, ())
    updCommand.name = "HusqvarnaControl"
    updCommand.start()      

#Husqvarna
class mower:
    hqAuth_url = ""
    hqurl = ""
    hqCmdUrl = ""
    hqapikey = ""
    hqauth  = ""
    name = []
    bat = []
    status = []
    error = []
    doorCnt = 0
    time=0
    timer=0
    run=0
    polltime=30
    time_alert=""

    def update(self):
        while True:
            self.polltime = POLL_TIME
            #Get Mower Status
            print("Poll Husqvarna")
            try:            
                #Authenticate Husqvarna
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                
                response = requests.post(self.hqAuth_url,  verify=True, data=self.hqauth, headers=headers, timeout=10).json()
                
                id_ = response['access_token']
                mwresponse = requests.get(self.hqurl, headers={'Authorization': 'Bearer ' + id_, 'Authorization-Provider': 'husqvarna', 'X-Api-Key': self.hqapikey}, timeout=15).json()
                #print(mwresponse)
                self.movError = "Unable to connect"
                with dataLock:
                    for cnt in range (0,len(mwresponse['data'])):
                        if len(self.name) > cnt:
                            self.name[cnt] = mwresponse['data'][cnt]['attributes']['system']['name']
                            #print(self.name[cnt])
                            movstat = mwresponse['data'][cnt]['attributes']['mower']['state']
                            movconn = mwresponse['data'][cnt]['attributes']['mower']['activity']
                            self.bat[cnt] = mwresponse['data'][cnt]['attributes']['battery']['batteryPercent']
                            if (movconn == "NOT_APPLICABLE"):
                                self.status[cnt] = MOVER_STATE.get(movstat)        
                            else:
                                self.status[cnt] = MOVER_ACTIVITY.get(movconn)
                            self.error[cnt] = MOVER_ERROR.get(mwresponse['data'][cnt]['attributes']['mower']['errorCode'])
                        else:
                            self.name.append(mwresponse['data'][cnt]['attributes']['system']['name']) 
                            #print(self.name[cnt])
                            movstat = mwresponse['data'][cnt]['attributes']['mower']['state']
                            movconn = mwresponse['data'][cnt]['attributes']['mower']['activity']
                            self.bat.append(mwresponse['data'][cnt]['attributes']['battery']['batteryPercent'])
                            if (movconn == "NOT_APPLICABLE"):
                                self.status.append(MOVER_STATE.get(movstat))        
                            else:
                                self.status.append(MOVER_ACTIVITY.get(movconn))
                            self.error.append(MOVER_ERROR.get(mwresponse['data'][cnt]['attributes']['mower']['errorCode']))

                self.time = datetime.datetime.now().strftime("%H:%M")
                self.timer = time.time()

            except:
                print("Husqvarna has failed")
                self.polltime = 3600
                print("Waiting to poll for 1 hours")

            time.sleep(self.polltime)                    
            self.run = 0
        
        #updHusqvarna = threading.Timer(POLL_TIME, Husqvarna, ())
        #updHusqvarna.start()      

#******************************************** Octoprint monitor **********************************
def octoprint():
    global updOcto
    global octoresp
    global d_state
    global d_percent
    global d_file
    global d_time
    global d_timeleft    
   
    try:
        octoresp = requests.get("http://192.168.1.235/api/job?apikey=CAD50F8FB9AF45F78D490206E5FA4690", timeout=10).json()
        #print(octoresp)
            
        with dataLock:
            if 'state' in octoresp:
                d_state=octoresp['state']
                d_percent=octoresp['progress']['completion']
                d_file=octoresp['job']['file']['name']
                d_file = d_file.replace('FCPRO_', '')
                d_file = d_file.replace('.gcode', '')
                d_file = d_file[:1].upper() + d_file[1:].lower()
                d_time=octoresp['progress']['printTime']
                d_timeest=octoresp['job']['estimatedPrintTime']
                #d_timeleft = d_timeest-d_time
                d_timeleft=octoresp['progress']['printTimeLeft']
                if d_timeleft<0:
                    d_timeleft=0
                if (d_state == "Printing"):
                    d_percent = (d_time / (d_time + d_timeleft))*100
                else:
                    d_percent = 0
                                
            else:
                d_state=""
                d_percent=0
                d_file=""
                d_time=0
                d_timeleft=0
                                
    except:
        d_state=""
        d_percent=0
        d_file=""
        d_time=0
        d_timeleft=0
        #print("Octoprint not connected")
        time.sleep(POLL_TIME_OCT)

    print("Initiate Octoprint")
    updOcto = threading.Timer(POLL_TIME_OCT, octoprint, ())
    updOcto.name = "Octoprint"
    updOcto.start()      
        
#******************************************************** News ****************************************************        
def News():
    global updNews
    global data3
       
    try:
        time_ = datetime.datetime.now()
        response = requests.get('http://www.svt.se/nyheter/rss.xml', timeout=15)
        #response = requests.get('https://gnews.io/api/v4/top-headlines?token=1fec0ecb72f926bdde74899284f39532&&topic=breaking-news&max=5&country=se', timeout=15).json()
#    except:
#        print("Could not retreive news")
#        updNews = threading.Timer(POLL_TIME_NEWS, News, ())
#        updNews.start()
        
        with dataLock:    
           content = io.BytesIO(response.content)
           feed = feedparser.parse(content)
           # headlines=[]
       
           if 'entries' in feed:
                 #data3 = response
               data3 = feed
    except:
        print("News Task Failed")
    
    #return data
    updNews = threading.Timer(POLL_TIME_NEWS, News, ())
    updNews.name = "News"
    updNews.start()
        
#***************************************************** Weather **********************************************        
def Weather_Forecast():
    global updWeather
    global data2

    try:
        time_ = datetime.datetime.now()
        response = requests.get("http://api.openweathermap.org/data/2.5/forecast?q=staffanstorp,SE&appid="+API_KEY + "&units=metric", timeout=15).json()
#    except:
#        print("Could not retreive weather")
#        updWeather = threading.Timer(POLL_TIME_WEATHER, Weather_Forecast, ())
#        updWeather.start()
    
        with dataLock:   
            data2 = [ ]
            cnt=0
            currday=""
            cntday=0
            min=99
            max=-99
            rain=0
            
            #while cntday < 5:
            for cnt in range(response['cnt']+1):
                if cnt < response['cnt']:
                    newday = datetime.datetime.strptime(str(response['list'][cnt]['dt_txt']), '%Y-%m-%d %H:%M:%S').strftime("%A");
                    newhour = datetime.datetime.strptime(str(response['list'][cnt]['dt_txt']), '%Y-%m-%d %H:%M:%S').strftime("%H");
                else:
                    newday = "End"
                    
                if currday != newday and currday != "":
                    data2.append({
                    'cnt': response['cnt'],
                    'day': currday,
                    'temp_min': "{:10.0f}".format(min), 
                    'temp_max': "{:10.0f}".format(max), 
                    'wind': "{:10.0f}".format(wind), 
                    'rain': "{:10.0f}".format(rain), 
                    'desc': str(desc), 
                    'icon': "http://openweathermap.org/img/w/" + str(icon) + ".png",
                    'weather_time': time_.strftime("%H:%M")
                    })
                    cntday = cntday + 1
                    min=99
                    max=-99
                    rain=0
                else:                  
                    if response['list'][cnt]['main']['temp_min'] < min:
                        min = response['list'][cnt]['main']['temp_min']
                    if response['list'][cnt]['main']['temp_max'] > max:
                        max = response['list'][cnt]['main']['temp_max']
                    if 'rain' in response['list'][cnt]:
                        rain = rain + response['list'][cnt]['rain']['3h']
                    
                    if newhour == '15' or currday == "":
                        wind = response['list'][cnt]['wind']['speed']
                        icon = response['list'][cnt]['weather'][0]['icon']
                        desc = response['list'][cnt]['weather'][0]['description']
                        currhour = newhour
            
                cnt = cnt + 1
                currday = newday
            
        if 'cnt' not in data2:
             data2.append({ 'cnt': 0 })
         
    except:
        print("Weather Task Failed")

    #Return data
    print("Initiate Weather")
    updWeather = threading.Timer(POLL_TIME_WEATHER, Weather_Forecast, ())
    updWeather.name = "Weather"
    updWeather.start()

#******************************* Shelly ***************************************
class sh:
    relay=False
    relay_set='' 
    ip=''
    kw=float(0)
    temp=float(0)
    hum=float(0)
    bat=0
    time=0
    timer=0

    def update(self):

        while True:
            print("Poll Shelly")
            #Update relay status
            try:
                if self.relay_set == 'on':
                    resp = requests.get(url=self.ip+'/relay/0?turn=on', timeout=15).json()
                elif self.relay_set == 'off':
                    resp = requests.get(url=self.ip+'/relay/0?turn=off', timeout=15).json()   
                self.relay_set = ''
            except:
                print("Shelly device update failed")

            #Retrieve relay status
            try:
                resp = requests.get(url=self.ip+'/status', timeout=15).json()

                self.relay = resp['relays'][0]['ison']
                self.kw = resp['meters'][0]['power']
                self.temp = resp['temperature']
            except:
                print("Shelly device failed to respond")
    
            time.sleep(POLL_TIME_SH)

#************************************* Telldus Live *******************************************
def TelldusLive():
    global updTelldus       
    
    telldus.time = datetime.datetime.now().strftime("%H:%M")
    telldus.timer = time.time()
            
    #Update Teldus
    try: 
        telldus.con_temp = GetSensor('Conservatory', 'temp', 'value')
        telldus.con_hum = GetSensor('Conservatory', 'humidity', 'value')
        telldus.in_temp = float(GetSensor('Inside', 'temp', 'value'))
        telldus.in_hum = GetSensor('Inside', 'humidity', 'value')
    except:
        print("Telldus failed")
    
    print("Initiate Telldus")
    updTelldus = threading.Timer(POLL_TIME_TELL, TelldusLive, ())
    updTelldus.name="Telldus"
    updTelldus.start()   
                
#Telldus Authenticate            
def Authenticate():
    global oauth

    oauth = OAuth1(Public_key,
                   client_secret=Private_key,
                   resource_owner_key=Token,
                   resource_owner_secret=Token_secret)
    return 

#Telldus Get Sensors
def GetSensor(name_, type_, value_):
    
    #Get List of Sensors
    try: 
        response_sensors = requests.get(url=protected_url+'sensors/list', auth=oauth, timeout=15).json()
    except:
        #print(response_sensors)
        print("Telldus API failed Sensor")
        return 

    #Parser sensor list to find sensor by name
    count = 0
    id_ = 0
    while id_ == 0 and count < len(response_sensors['sensor']):
        if response_sensors['sensor'][count]['name'] == name_ and response_sensors['sensor'][count]['client'] == Client_id:
            id_ = response_sensors['sensor'][count]['id']
        count = count + 1

    #Retrieve sensor details
    try:
        response = requests.get(url=protected_url+'sensor/info?id=' + id_, auth=oauth, timeout=15).json()
    except:
        return 
        
    #Parse sensor details to get value by name
    count = 0
    res_ = ''
    while res_ == '' and count < len(response['data']):
        if (response['data'][count]['name'] == type_):
            res_ = response['data'][count][value_]
        count = count + 1

    #print(res_)
    
    return res_

#Telldus Get Devices
def GetDevice(name_, type_, value_):
    #global response_devices
    
    try:
        response_devices = requests.get(url=protected_url+'devices/list', auth=oauth, timeout=15).json()
    except:
        print("Telldus API failed Device")
        print(response_devices)
        print(protected_url)
        return 
    
    count = 0
    id_ = 0
    while id_ == 0 and count < len(response_devices['device']):
        if response_devices['device'][count]['name'] == name_ and response_devices['device'][count]['client'] == Client_id:
            id_ = response_devices['device'][count]['id']
        count = count + 1

    try:
        response = requests.get(url=protected_url+'device/info?id=' + id_ + '&supportedMethods=3', auth=oauth, timeout=15).json()
    except:
        return 
        
    res_ = response[value_]
    
    return res_

  
#************************************************** PIR ******************************************
def pir():
    global updPir
    global display
    global display_timer
    global menupage
    global timerVoice
    
    while True:
        try:
            with dataLock:   
                prox = GPIO.input(PIR_PIN)
        
                if (prox == 1 and display == 0):
                    subprocess.call("sh disp_on.sh", shell=True)
                    #print("Display On")
                    display = 1

                if (prox == 0 and display == 1 and display_timer >= 30):
                    subprocess.call("sh disp_off.sh", shell=True)
                    display = 0
            
                if (prox == 0 and display == 1):
                    display_timer = display_timer + 1
                else:
                    display_timer = 0
                    #prox = 0;
                    
                #Voice recognition
                CMDID = DF2301Q.get_CMDID()
                if CMDID != 0:
                    if (CMDID == 5):
                        menupage = 1
                    elif (CMDID == 6):
                        menupage = 0
                    elif (CMDID == 7):
                        pool.sauna_cmd = "1"
                    elif (CMDID == 8):
                        pool.sauna_cmd = "2"        

                    print("Voice command = " + str(CMDID))                        
                
        except:
            print("PIR Task Failed")
        
        time.sleep(POLL_TIME_PIR)

#***************************** Log Data to MySQL *********************************************
def logdata():
    now = datetime.datetime.now()
    logv.time = datetime.datetime.now().strftime("%H:%M")
    logv.timer = time.time()
    currDateTime = datetime.datetime.strftime(now, '%Y-%m-%d %H:%M')
    currDate = datetime.datetime.strftime(now, '%Y-%m-%d')

    #Calculate hour values
    if (energymeter.energy_meter > 0):
        logv.energy_hour = energymeter.energy_meter - logv.energymeter_lasthour
    if (energymeter.energy_meter_prod > 0):
        logv.energy_hour_prod = energymeter.energy_meter_prod - logv.energymeter_lasthour_prod
    if (Huawei_SUN2000.acc_yield > 0 and logv.solar_lasthour > 0):
        logv.solar_hour = Huawei_SUN2000.acc_yield - logv.solar_lasthour
    if (energymeter2.energy_meter > 0):
        logv.energy2_hour = energymeter2.energy_meter - logv.energymeter2_lasthour

        #Set default values
        if (logv.energymeter2h_lasthour == 0):
            logv.energymeter2h_lasthour = energymeter2.energy_meter
        if (logv.energymeter2w_lasthour == 0):
            logv.energymeter2w_lasthour = energymeter2.energy_meter          
        
        if (hp.mode == 'Heat'):
            logv.energy2h_hour =  energymeter2.energy_meter - logv.energymeter2h_lasthour
        else:
            logv.energymeter2h_lasthour = energymeter2.energy_meter - logv.energy2h_hour

        if (hp.mode == 'Hot water'):
            logv.energy2w_hour =  energymeter2.energy_meter - logv.energymeter2w_lasthour
        else:
            logv.energymeter2w_lasthour = energymeter2.energy_meter - logv.energy2w_hour
    
    if (water.value > 0 and logv.water_lasthour > 0 and logv.water_lasthour < water.value):
        logv.water_hour = water.value - logv.water_lasthour

    if (charger1.meter > 0):
            logv.ch1_hour = charger1.meter - logv.ch1_lasthour

    # if (charger1.totalConsumptionKwh > 0 and (charger1.totalConsumptionKwh - logv.ch1_lasthour) > 0):
    #     logv.ch1_hour = charger1.totalConsumptionKwh - logv.ch1_lasthour
    #     logv.ch1_lastId = charger1.sessionId

    # if (charger1.sessionId != logv.ch1_lastId and charger1.sessionId != None):
    #     charger1.meter = logv.ch1_lasthour + logv.ch1_hour
    #     logv.ch1_lastId = charger1.sessionId

    # if (charger1.totalConsumptionKwh > 0):
    #      logv.ch1_hour = (charger1.meter + charger1.totalConsumptionKwh) - logv.ch1_lasthour  
    #      logv.ch1_lastId = charger1.sessionId
    
    #print("Total: " + str(charger1.totalConsumptionKwh))
    #rint("Hour: " + str(logv.ch1_hour))
    #print("LastHour: " + str(logv.ch1_lasthour))
    if (castle.energy_meter > 0):
        logv.c_energy_hour = castle.energy_meter - logv.c_energymeter_lasthour

    #Update MySQL
    cursor = db.cursor()
    cursor.execute("select energy_meter from energy where year=%s and month=%s and day=%s and hour=%s", (now.year, now.month, now.day, now.hour))
    data = cursor.fetchone()

    if (data):
        #udpdate
        sql = "update energy set datetime=%s, energy_meter=%s, energy_hour=%s, energy_meter_prod=%s, energy_hour_prod=%s, castle_meter=%s, castle_hour=%s, energy_meter2=%s, energy2_hour=%s, energy2w_hour=%s, energy2h_hour=%s, price=%s, netprice=%s, solar_meter=%s, solar_hour=%s, water_meter=%s, water_hour=%s, ch1_hour=%s, ch1_meter=%s, ch1_id=%s , debug=%s where year=%s and month=%s and day=%s and hour=%s" 
        val = (currDateTime, energymeter.energy_meter, logv.energy_hour, energymeter.energy_meter_prod, logv.energy_hour_prod, castle.energy_meter, logv.c_energy_hour, energymeter2.energy_meter, logv.energy2_hour, logv.energy2w_hour, logv.energy2h_hour,  tb.price, tb.netprice, logv.solar_lasthour, logv.solar_hour, water.value, logv.water_hour, logv.ch1_hour, charger1.meter, charger1.sessionId, "LOG Update",now.year, now.month, now.day, now.hour)
        #DEMO cursor.execute(sql, val)
        #DEMO db.commit()
    else:
        #Insert 
        sql = "INSERT INTO energy (datetime, year, month, day, hour, type, energy_meter, energy_hour, energy_meter_prod, energy_hour_prod, castle_meter, castle_hour, energy_meter2, energy2_hour, energy2w_hour, energy2h_hour, price, netprice, outside_temp, solar_meter, solar_hour, water_meter, water_hour, ch1_hour, ch1_meter, ch1_id, debug) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (currDateTime, now.year, now.month, now.day, now.hour, 'hour', energymeter.energy_meter, logv.energy_hour, energymeter.energy_meter_prod, logv.energy_hour_prod, castle.energy_meter, logv.c_energy_hour, energymeter2.energy_meter, logv.energy2_hour, logv.energy2w_hour, logv.energy2h_hour, tb.price, tb.netprice, hp.outdoor, logv.solar_lasthour, logv.solar_hour, water.value, logv.water_hour,logv.ch1_hour, charger1.meter, charger1.sessionId, "LOG Insert")
        #DEMO cursor.execute(sql, val)
        #DEMO db.commit()

    if (now.hour != logv.lasthour):
        if (energymeter.energy_meter > 0):
            logv.energymeter_lasthour = energymeter.energy_meter
        if (energymeter.energy_meter_prod > 0):
            logv.energymeter_lasthour_prod = energymeter.energy_meter_prod
        if (Huawei_SUN2000.acc_yield > 0):
            logv.solar_lasthour = Huawei_SUN2000.acc_yield
        if (water.value > 0):
            logv.water_lasthour = water.value
        if (charger1.meter > 0):
            logv.ch1_lasthour = charger1.meter

        if (energymeter2.energy_meter > 0):
            logv.energymeter2_lasthour = energymeter2.energy_meter
            logv.energy2h_hour = 0
            logv.energy2w_hour = 0
            logv.energymeter2h_lasthour = energymeter2.energy_meter
            logv.energymeter2w_lasthour = energymeter2.energy_meter
        if (castle.energy_meter > 0):
            logv.c_energymeter_lasthour = castle.energy_meter
        logv.lasthour = now.hour
        tb.price=tb.nextprice

    #Estimate the month consumption
    cursor.execute("select sum(energy_hour), sum(castle_hour), sum(energy2_hour), count(*), sum(energy_hour_prod), sum(solar_hour), sum(ch1_hour), sum(ch1_hour/1000*price) from energy where year=%s and month=%s group by month", (now.year, now.month) )
    data = cursor.fetchone()

    if (data):
        energymeter.month = data[0]
        energymeter.month_est = data[0] / data[3] * calendar.monthrange(now.year, now.month)[1] * 24 / 1000
        energymeter.month_est2 = data[1] / data[3] * calendar.monthrange(now.year, now.month)[1] * 24  / 1000      
        #energymeter2.month_est = data[2] / data[3] * calendar.monthrange(now.year, now.month)[1] * 24 / 1000
        energymeter.month_est_tot = (float(data[5]*1000) - float(data[4]) + data[0] ) / data[3] * calendar.monthrange(now.year, now.month)[1] * 24 / 1000
        energymeter.month_prod = float(data[4])
        charger1.month_consumption = float(data[6])
        charger1.month_cost = float(data[7]) + (float(data[6]/1000) * float(((ELNET_PRICE + ELNET_TAX) * 1.25))) 
        
    cursor.execute("select sum(energy2_hour), sum(energy2h_hour), count(*) from energy where year=%s and month=%s and energy2_hour is not null group by month", (now.year, now.month) )
    data = cursor.fetchone()

    if (data):
        energymeter2.month_est = data[0] / data[2] * calendar.monthrange(now.year, now.month)[1] * 24 / 1000
        energymeter2.month_est2 = data[1] / data[2] * calendar.monthrange(now.year, now.month)[1] * 24 / 1000
        
    #Estimate daily consumption
    cursor.execute("select sum(energy_hour), sum(castle_hour), sum(energy2_hour), count(*), sum(energy_hour_prod), sum(solar_hour), sum(ch1_hour) from energy where year=%s and month=%s and day=%s group by day", (now.year, now.month, now.day))
    data = cursor.fetchone()
    
    if (data):
        energymeter.day_est = (((data[0]-float(data[6])) / data[3] * 24) + float(data[6]))/ 1000
        energymeter.day_est2 = data[1] / data[3] * 24 / 1000
        energymeter.day = data[0] / 1000
        energymeter.day_est_net = energymeter.day_est -  (float(data[4]) / 1000)
        #energymeter2.day_est = data[2] / data[3] * 24 / 1000
        energymeter.day_est_tot = (float(data[5]*1000) - float(data[4]) + data[0] )  / data[3] * 24 / 1000
        energymeter.day_prod = (float(data[4]) / 1000)

    cursor.execute("select sum(energy2_hour), sum(energy2h_hour), count(*) from energy where month=%s and day=%s and energy2_hour is not null group by day", (now.month,now.day))
    data = cursor.fetchone()

    if (data):
        #print(data)
        energymeter2.day_est = data[0] / data[2] * 24 / 1000
        energymeter2.day_est2 = data[1] / data[2] * 24 / 1000

    #Estimate yearly consumption
    cursor.execute("select month, sum(energy_hour), count(*), sum(energy_hour_prod), sum(solar_hour)  from energy where (year=%s and month<%s) or (year=%s and month>=%s) group by month", (now.year, now.month, now.year-1, now.month))
    data = cursor.fetchall()
    val = 0
    val2 = 0
    cnt = 0
    for doc in data:
        val = val + ( (doc[1] / doc[2] * calendar.monthrange(now.year, doc[0])[1] * 24 / 1000) * (100/avgConsumption[(doc[0]-1)]) )
        if doc[3] != None and doc[4] != None:
            val2 = val2 + ( ((float(doc[4]*1000) - float(doc[3]) + doc[1] ) / doc[2] * calendar.monthrange(now.year, doc[0])[1] * 24 / 1000) * (100/avgConsumption[(doc[0]-1)]) )
        cnt = cnt + 1
    energymeter.year_est = val / cnt
    energymeter.year_est_tot = val2 / cnt
    
    #Monthly production
    cursor.execute("select sum(solar_hour) from energy where year=%s and month=%s", (now.year,now.month))
    data = cursor.fetchone()
    
    if (data):
        Huawei_SUN2000.monthly_yield = data[0]
        #print(Huawei_SUN2000.monthly_yield)

    #Monthly earnings
    #cursor.execute("select sum(energy_hour_prod/1000 * ((price/1.34) + 0.1) ) from energy where month=%s", (now.month))
    cursor.execute("select sum(energy_hour_prod/1000 * (NVL(netprice, (price*0.80) - %s) + %s) ), sum((energy_hour/1000) * (NVL(netprice, (price*0.80) - %s) + %s)*1.25), sum(energy_hour/1000) from energy where year=%s and month=%s", (EL_PURCH+EL_CERT+EL_ADDON, SOLAR_BONUS,  EL_PURCH+EL_CERT+EL_ADDON, EL_PURCH+EL_CERT+EL_ADDON, now.year, now.month))
    data = cursor.fetchone()

    if (data):
        Huawei_SUN2000.monthly_earned = data[0] + (((tb.netprice) + SOLAR_BONUS) * logv.energy_hour_prod / 1000)
        Huawei_SUN2000.monthly_payed = data[1] + ( (tb.netprice + EL_PURCH+EL_CERT+EL_ADDON) * 1.25 * logv.energy_hour / 1000) + EL_MON
        Huawei_SUN2000.monthly_payed_net = (data[2] * ((ELNET_PRICE + ELNET_TAX) * 1.25)) - (data[0] * SOLAR_NET) + ELNET_MON 
        #print(Huawei_SUN2000.monthly_earned)

    #Yearly production
    cursor.execute("select sum(solar_hour) from energy where (year=%s and month<%s) or (year=%s and month=%s and day<%s) or (year=%s and month=%s and day=%s and hour<%s) or (year=%s and month>%s) or (year=%s and month=%s and day>%s) or (year=%s and month=%s and day=%s and hour>=%s)", (now.year, now.month, now.year, now.month, now.day,  now.year, now.month, now.day, now.hour, now.year-1, now.month, now.year-1, now.month, now.day, now.year-1, now.month, now.day,now.hour))
    data = cursor.fetchone()
    
    if (data):
        Huawei_SUN2000.yearly_yield = float(data[0])

    #Current day data
    cursor.execute("select energy_hour, solar_hour from energy where year=%s and month=%s and day=%s", (now.year,now.month,now.day))
    data = cursor.fetchall()
    
    cnt = 0
    energymeter.day_arr= [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ]
    Huawei_SUN2000.day_arr= [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ]
    for doc in data:
        energymeter.day_arr[cnt] = doc[0]
        Huawei_SUN2000.day_arr[cnt] = doc[1]
        cnt = cnt + 1
        
    print("Initiate log")
    updLg = threading.Timer(POLL_TIME_LG, logdata, ())
    updLg.name="Log"
    updLg.start()


#***************************************** asyncIO Loop **************************************
def asyncLoop():
    global sSummer
    global sPool
    global sMeter
    global sMeter2

    while True:
        loop.run_until_complete(thermia())
        loop.run_until_complete(Huawei_SUN2000.update())
        
        global debug

        print("Threadcount: " + str(threading.active_count()))
        debug = "Threadcount: " + str(threading.active_count())        

        time.sleep(POLL_TIME_ASYNC)
       

def ThreadCleanup():
        killThread = ""
        
        while True:
            try:
                for thread in threading.enumerate():
                    print(thread.name)
                    if  thread.name.find("Thread-") >= 0:
                        if killThread == "":
                            killThread = thread.name
                            Print("Found thread to kill")
                            print(thread.name)
                        else:
                            killThread = ""
                            print("Kill Thread ")
                            print(thread.name)
                            #thread.join()
            except:
                print("Crash")
            time.sleep(30)


async def thermia():
    global tdata 

    #while True:
    print("Await Thermia")

    thermia = pythermiagenesis.ThermiaGenesis(HOST, port=PORT, kind="inverter", delay=0.15)
        
    now = datetime.datetime.now()
    hp.time = datetime.datetime.now().strftime("%H:%M")
    hp.timer = time.time()

    if tb.price > PRICE_MAX:
        hp.price_adj = -2
    elif tb.price > tb.price_break and tb.price > PRICE_MIN and tb.price > tb.price_avg:
        hp.price_adj = -1
    elif tb.price < PRICE_OK and hp.room_temp < HEAT_TEMP :
        hp.price_adj = 1
    else:
        hp.price_adj = 0
        
    if hp.lasthour != now.hour:        
        if weather.wind > 12 and hp.room_temp < HEAT_TEMP:
            hp.wind_adj = 2
        elif weather.wind > 6 and hp.room_temp < HEAT_TEMP:
            hp.wind_adj = 1
        else:
            hp.wind_adj = 0
    hp.temp_set = HEAT_TEMP + hp.wind_adj + hp.price_adj
    hp.lasthour = now.hour

    try:
        #await thermia.async_set('coil_enable_tap_water', False)

        if hp.temp_set != hp.temp_set_last:
            #await thermia.async_set('coil_enable_heat', hp.heat_on)
            await thermia.async_set('holding_comfort_wheel_setting', hp.temp_set)
            #print("Setting temp to " + str(hp.temp_set) + " wind:" + str(hp.wind_adj) + " price:" + str(hp.price_adj))
        hp.temp_set_last = hp.temp_set
    
        await thermia.async_update(only_registers=[
            'input_outdoor_temperature',
            'input_first_prioritised_demand',
            'input_electric_meter_meter_value',
            'input_electric_meter_kwh_total',
            'input_compressor_speed_rpm',
            'input_condenser_in_temperature',
            'input_condenser_out_temperature',
            'input_tap_water_top_temperature',
            'input_discharge_pipe_temperature', 
            'input_brine_in_temperature', 
            'input_brine_out_temperature', 
            'input_compressor_speed_percent',
            'input_compressor_operating_hours',
            'input_room_temperature_sensor',
            #'input_compressor_operating_hours_msb',
            #'input_compressor_operating_hours_lsb',
            'input_tap_water_operating_hours',
            #'input_tap_water_operating_hours_msb',
            #'input_tap_water_operating_hours_lsb',
            'input_external_additional_heater_operating_hours',
            'input_low_pressure_side',
            'input_high_pressure_side',
            'dinput_sum_alarm',
            'dinput_alarm_active_class_a',
            'dinput_alarm_active_class_b',
            'dinput_alarm_active_class_c',
            'dinput_high_pressure_switch_alarm',
            'dinput_low_pressure_level_alarm',
            'dinput_high_discharge_pipe_temperature_alarm',
            'dinput_operating_pressure_limit_indication',
            'dinput_discharge_pipe_sensor_alarm',
            'dinput_liquid_line_sensor_alarm',
            'dinput_suction_gas_sensor_alarm',
            'dinput_flow_pressure_switch_alarm',
            'dinput_power_input_phase_detection_alarm',
            'dinput_inverter_unit_alarm',
            'dinput_system_supply_low_temperature_alarm',
            'dinput_compressor_low_speed_alarm',
            'dinput_low_super_heat_alarm',
            'dinput_pressure_ratio_out_of_range_alarm',
            'dinput_compressor_pressure_outside_envelope_alarm',
            'dinput_brine_temperature_out_of_range_alarm',
            'dinput_brine_in_sensor_alarm',
            'dinput_brine_out_sensor_alarm',
            'dinput_condenser_in_sensor_alarm',
            'dinput_condenser_out_sensor_alarm',
            'dinput_outdoor_sensor_alarm',
            'dinput_system_supply_line_sensor_alarm',
            'dinput_mix_valve_1_supply_line_sensor_alarm',
            'dinput_mix_valve_2_supply_line_sensor_alarm',
            'dinput_mix_valve_3_supply_line_sensor_alarm',
            'dinput_mix_valve_4_supply_line_sensor_alarm',
            'dinput_mix_valve_5_supply_line_sensor_alarm',
            'dinput_twc_supply_line_sensor_alarm',
            'dinput_cooling_supply_line_sensor_alarm',
            'dinput_brine_delta_out_of_range_alarm',
            'dinput_tap_water_mid_sensor_alarm',
            'dinput_twc_circulation_return_sensor_alarm',
            'dinput_hgw_sensor_alarm',
            'dinput_internal_additional_heater_alarm',
            'dinput_brine_in_high_temperature_alarm',
            'dinput_brine_in_low_temperature_alarm',
            'dinput_brine_out_low_temperature_alarm',
            'dinput_twc_circulation_return_low_temperature_alarm',
            'dinput_twc_supply_low_temperature_alarm',
            'dinput_mix_valve_1_supply_temperature_deviation_alarm',
            'dinput_mix_valve_2_supply_temperature_deviation_alarm',
            'dinput_mix_valve_3_supply_temperature_deviation_alarm',
            'dinput_mix_valve_4_supply_temperature_deviation_alarm',
            'dinput_mix_valve_5_supply_temperature_deviation_alarm',
            'dinput_sum_alarm',
            'dinput_temperature_room_sensor_alarm',
            'dinput_inverter_unit_communication_alarm',
            'dinput_pool_return_line_sensor_alarm',
            'dinput_external_stop_for_pool',
            'dinput_external_start_brine_pump',
            'dinput_tap_water_end_tank_sensor_alarm',
            'dinput_maximum_time_for_anti_legionella_exceeded_alarm',
            'input_system_supply_line_calculated_set_point',
            'input_system_supply_line_temperature',
            'input_condenser_circulation_pump_speed',
            'dinput_brine_pump_on_off_control',
            'dinput_system_circulation_pump_control_signal',
            'dinput_condenser_pump_on_off_control',
            'dinput_compressor_control_signal',
            'dinput_mix_valve_1_circulation_pump_control_signal',
            'dinput_twc_supply_line_circulation_pump_control_signal',
            'dinput_internal_additional_heater_active',
            'input_selected_heat_curve',

            'holding_comfort_wheel_setting'
            ])

    except (pythermiagenesis.ThermiaConnectionError) as error:
        print(f"Failed to connect: {error.message}")
        #return
    except (ConnectionError) as error:
        print(f"Connection error {error}")
        #return

    if thermia.available:
        tdata = thermia.data 

        #Adjust the comfort setting depending on energy price and wind factor
        hp.outdoor = tdata['input_outdoor_temperature']
        hp.mode = tdata['input_first_prioritised_demand']
        hp.return_line = tdata['input_condenser_in_temperature']
        hp.supply_line = tdata['input_condenser_out_temperature']
        hp.brine_in = tdata['input_brine_in_temperature']
        hp.brine_out = tdata['input_brine_out_temperature']
        hp.water = tdata['input_tap_water_top_temperature']
        hp.compressor_runtime = tdata['input_compressor_operating_hours']
        hp.room_temp = tdata['input_room_temperature_sensor']
        hp.water_runtime = tdata['input_tap_water_operating_hours']
        hp.heater_runtime = tdata['input_external_additional_heater_operating_hours']
        hp.compressor_speed = tdata['input_compressor_speed_rpm']
        hp.compressor_precent = tdata['input_compressor_speed_percent']
        hp.alarm = tdata['dinput_sum_alarm']
        hp.low_pressure = tdata['input_low_pressure_side']
        hp.high_pressure = tdata['input_high_pressure_side']
        hp.supply_req = tdata['input_system_supply_line_calculated_set_point']
        hp.condens_pump_speed = tdata['input_condenser_circulation_pump_speed']
        hp.brine_pump = tdata['dinput_brine_pump_on_off_control']
        hp.circ_pump = tdata['dinput_system_circulation_pump_control_signal']
        hp.condens_pump = tdata['dinput_condenser_pump_on_off_control']
        hp.compressor = tdata['dinput_compressor_control_signal']
        hp.mix_valve_pump = tdata['dinput_mix_valve_1_circulation_pump_control_signal']
        hp.twc_supply_pump = tdata['dinput_twc_supply_line_circulation_pump_control_signal']
        hp.extra_heater = tdata['dinput_internal_additional_heater_active']
        hp.heat_curve = tdata['input_selected_heat_curve']
        hp.temp_set = tdata['holding_comfort_wheel_setting']
        #'input_system_supply_line_temperature',
    
        if (hp.alarm == True):
            for item in tdata:
                x = item.find("alarm")
                if x > 0 and tdata[item] == True:
                    hp.alarm_msg = item.replace("dinput_","").replace("_"," ").replace(" alarm","").capitalize()
        #print(hp.alarm_msg)
            
        #await asyncio.sleep(POLL_TIME_HEAT)

#************************************* Solar Inverter *****************************************
class solar:
    ip  = ""
    client = None
    slave_id = 0
    port = 0
    energy = float(0)
    device_status = ""
    temp = float(0)
    grid_acc = float(0)
    power_meter = float(0)
    daily_yield = float(0)
    acc_yield = float(0)
    pv1_v = float(0)
    pv1_a = float(0)
    pv2_v = float(0)
    pv2_a = float(0)
    input_power = float(0)
    daily_power_peak = float(0)
    fault_code = ""
    monthly_yield = float(0)
    monthly_earned = float(0)
    monthly_payed = float(0)
    monthly_payed_net = float(0)
    yearly_yield = float(0)
    time = 0
    timer = 0
    time_alert = ""
    day_arr = [ 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0 ]


    async def update(self):

        #while True:
        print("Await Solar")
        
        if self.client is None:
            try:
                print("Connect to Huawei")
                self.client = await AsyncHuaweiSolar.create(self.ip, self.port, self.slave_id)
            except:        
                print("Connection to Huawei failed")
                await AsyncHuaweiSolar.stop(self.client)
                self.client = None
                self.energy = float(0)
                return

        if self.client is not None:
            print("Retreive data from Huawei")
            # Reading a single register
            try:
                result = await self.client.get(rn.ACTIVE_POWER, self.slave_id)
                #print("Active Power: ", result.value)
                self.energy = result.value 
            except:
                print("Data retrieval failed from Huawei")
                await AsyncHuaweiSolar.stop(self.client)
                self.client = None
                self.energy = float(0)
                return

            try:
                result = await self.client.get(rn.DEVICE_STATUS, self.slave_id)
                #print("Device Status: ", result.value)
                self.device_status = result.value
            except:
                pass

            try:
                result = await self.client.get(rn.INTERNAL_TEMPERATURE, self.slave_id)
                #print("Temperature: ", result.value)
                self.temp = result.value
            except:
                pass

            try:
                result = await self.client.get(rn.DAILY_YIELD_ENERGY, self.slave_id)
                #print("Daily yield energy: ", result.value)
                self.daily_yield = result.value
            except:
                pass

            try:
                result = await self.client.get(rn.ACCUMULATED_YIELD_ENERGY, self.slave_id)
                #print("Acc yield energy: ", result.value)
                self.acc_yield = result.value * 1000   
            except:
                pass

            try:
                result = await self.client.get(rn.PV_01_VOLTAGE, self.slave_id)
                #print("PV1 Voltage: ", result.value)
                self.pv1_v = result.value
            except:
                pass
            
            try:
                result = await self.client.get(rn.PV_01_CURRENT, self.slave_id)
                #print("PV1 Current: ", result.value)
                self.pv1_a = result.value
            except:
                pass

            try:
                result = await self.client.get(rn.PV_02_VOLTAGE, self.slave_id)
                #print("PV2 Voltage: ", result.value)
                self.pv2_v = result.value
            except:
                pass

            try:
                result = await self.client.get(rn.PV_02_CURRENT, self.slave_id)
                #print("PV2 Current: ", result.value)
                self.pv2_a = result.value
            except:
                pass
    
            try:
                result = await self.client.get(rn.INPUT_POWER, self.slave_id)
                #print("Input Power: ", result.value)
                self.input_power = result.value
            except:
                pass

            try:
                result = await self.client.get( rn.DAY_ACTIVE_POWER_PEAK, self.slave_id)
                #print("Daily Power Peak: ", result.value)
                self.daily_power_peak = result.value
            except:
                pass

            try:
                result = await self.client.get(rn.FAULT_CODE, self.slave_id)
                #print("Fault Code: ", result.value)
                self.fault_code = result.value
            except:
                pass

            self.time = datetime.datetime.now().strftime("%H:%M")
            self.timer = time.time()

        await asyncio.sleep(POLL_TIME_HEAT)

class wm:
    ip = ""
    value = float(0)
    pre = float(0)
    raw = float(0)
    error = ""
    rate = float(0)
    timestamp = ""
    polltime = 0

    def update(self):
        while True:
            print("Poll Water")
        
            try:
                response = requests.get("http://" + self.ip + "/json", timeout=60).json()
                if (float(response['main']['value']) < 90000):
                    self.value = float(response['main']['value'])*1000
                self.pre = response['main']['pre']
                self.raw = response['main']['raw']
                self.error = response['main']['error']
                self.rate = response['main']['rate']
                self.timestamp = response['main']['timestamp']
                #{'main': {'value': '41.1315', 'raw': '00041.1315', 'pre': '41.1315', 'error': 'no error', 'rate': '0.000000', 'timestamp': '2023-06-19T18:56:49+0200'}}
                
            except:
                print("Error reading water meter")

            if self.rate == '':
                self.rate = float(0)

            #print(self.value)

            time.sleep(self.polltime)

def init_log():
    now = datetime.datetime.now()

    #Retrieve lastest meter values
    cursor = db.cursor()
    cursor.execute("select max(energy_meter), max(castle_meter), max(energy_meter2), max(energy_meter_prod), max(solar_meter), max(water_meter), max(ch1_meter), max(ch1_id) from energy where year=%s and month=%s", (now.year, now.month))
    data = cursor.fetchone()

    logv.energymeter_lasthour = int(data[0])
    logv.solar_lasthour = int(data[4])
    logv.energymeter_lasthour_prod = int(data[3])
    logv.c_energymeter_lasthour = int(data[1])
    logv.energymeter2_lasthour = int(data[2])
    logv.water_lasthour = int(data[5])
    logv.ch1_lasthour = int(data[6])
    logv.ch1_lastId = int(data[7])        

#******************************************** Charge Amp **************************************
class chargeamp:
    apikey = ""
    status = ""
    sessionId = 0
    lastSessionId = 0
    totalConsumptionKwh = float(0)
    lastTotalConsumptionKwh = float(0)
    polltime = 20
    month_consumption = 0
    month_cost = 0
    meter = 0

    def init(self):
        response = requests.post("https://eapi.charge.space/api/v4/auth/login",
                            headers={'apikey': self.apikey, 'authorization': self.apikey, 'Content-Type': 'application/json'},
                            json=self.auth, timeout=10).json()
        sessionToken = response['token']

        #Create charger meter value
        response = requests.get("https://eapi.charge.space/api/v4/chargepoints/" + charger1.id + "/chargingsessions", headers={'authorization': "Bearer " + sessionToken, 'Content-Type': 'application/json'}, timeout=30).json()
        for session in response:
            self.meter = self.meter + session['totalConsumptionKwh']
        self.meter = self.meter * 1000

        #Check current session, and substract current value
        response = requests.get("https://eapi.charge.space/api/v4/chargepoints/" + self.id + "/status", headers={'authorization': "Bearer " + sessionToken, 'Content-Type': 'application/json'}, timeout=30).json()
        if (response['connectorStatuses'][0]['sessionId'] != None):   
            self.lastTotalConsumptionKwh = response['connectorStatuses'][0]['totalConsumptionKwh'] * 1000
            self.sessionId = response['connectorStatuses'][0]['sessionId']

    def validateSessions(self):
        c1 = db2.cursor()

        response = requests.post("https://eapi.charge.space/api/v4/auth/login",
                            headers={'apikey': self.apikey, 'authorization': self.apikey, 'Content-Type': 'application/json'},
                            json=self.auth, timeout=10).json()
        sessionToken = response['token']

        #Validate all sessions
        response = requests.get("https://eapi.charge.space/api/v4/chargepoints/" + charger1.id + "/chargingsessions" + "?startTime=2023-09-01&endTime=2024-06-12", headers={'authorization': "Bearer " + sessionToken, 'Content-Type': 'application/json'}, timeout=30).json()
        for session in response:
            real = int(session['totalConsumptionKwh'] * 1000)
            id = session['id']
            if (real > 0):
                c1.execute("select sum(ch1_hour) from energy where ch1_id=%s", (id) )
                data = c1.fetchone()
                ch1 = data[0]
                if not data[0]:
                    print("Missing session " + str(id) + "/" + session['startTime'] + " " + str(real) + "kWh" )
                elif (ch1 != None):
                    if (real < ch1-100 or real > ch1+100):
                        print("Session missmatch updating" + str(id) + "/" + session['startTime'] + " " + str(real-ch1) + "kWh")

                        c1.execute("select max(id) from energy where ch1_id=%s and ch1_hour=0", (id) )
                        data = c1.fetchone()

                        if data[0]:
                            sql = "update energy set ch1_hour=%s, debug=%s where id=%s" 
                            val = (real-ch1, "Automatic Correction", data[0])
                        else:
                            c1.execute("select id,ch1_hour from energy where ch1_id=%s", (id) )
                            data = c1.fetchone()
                            hour = int(data[1])

                            sql = "update energy set ch1_hour=%s, debug=%s where id=%s" 
                            val = (hour + (real - ch1), "Automatic Correction", data[0])

                            print(val)

                        c1.execute(sql, val)
                        db2.commit()

        print("Check Done")


    def update(self):
        c1 = db2.cursor()

        while True:
            print("Poll ChargeAmp")
            try:
                response = requests.post("https://eapi.charge.space/api/v4/auth/login",
                                    headers={'apikey': self.apikey, 'authorization': self.apikey, 'Content-Type': 'application/json'},
                                    json=self.auth, timeout=10).json()
                sessionToken = response['token']

                response = requests.get("https://eapi.charge.space/api/v4/chargepoints/" + self.id + "/status", headers={'authorization': "Bearer " + sessionToken, 'Content-Type': 'application/json'}, timeout=30).json()

                #Save current values    
                self.status = response['connectorStatuses'][0]['status']
                if (response['connectorStatuses'][0]['totalConsumptionKwh'] > 0):
                    self.totalConsumptionKwh = response['connectorStatuses'][0]['totalConsumptionKwh'] * 1000
                self.sessionId = response['connectorStatuses'][0]['sessionId']

                #Add meter value
                if (self.totalConsumptionKwh > self.lastTotalConsumptionKwh):
                    self.meter = self.meter + (self.totalConsumptionKwh - self.lastTotalConsumptionKwh) 
                if (self.totalConsumptionKwh < self.lastTotalConsumptionKwh):
                    self.meter = self.meter + self.totalConsumptionKwh
                self.lastTotalConsumptionKwh = self.totalConsumptionKwh                    

            except:
                print("Error reading Charge Amps")
                
            time.sleep(self.polltime)
        
#***********************************************************************        
#***************************** Main ************************************       
#***********************************************************************       
if __name__ == "__main__":

    #Initiate 
    now = datetime.datetime.now()
    logv.lasthour = now.hour 
    Authenticate()

    #Initiate Shelly classes
    sh_pump = sh()
    sh_pump.ip = 'http://192.168.1.140'
    sh_clorinator = sh()
    sh_clorinator.ip = 'http://192.168.1.75'
    sh_workshop = sh()
    sh_workshop.ip = 'http://192.168.1.85'

    #Initiate Solar Classes
    Huawei_SUN2000 = solar()
    Huawei_SUN2000.ip = "192.168.1.204"
    Huawei_SUN2000.slave_id = 1
    Huawei_SUN2000.port = 502

    #Initate Charge Amps
    charger1 = chargeamp()
    charger1.polltime = 20
    charger1.apikey = XXXXXXXXXXXXXXXXXXXXXXXXX"
    charger1.auth = {"email": "<user>","password": "<psw>"}
    charger1.id = "XXXXXXXX"
    charger1.init()

    #Tibber
    tb = tibber()
    tb.location = 1
    tb.url = 'https://api.tibber.com/v1-beta/gql'
    tb.token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXj'
    tb.request = { "query": "{ viewer { homes { currentSubscription{ priceInfo{ current{ total energy tax startsAt } today { total energy tax startsAt } tomorrow { total energy tax startsAt } } } } } }" }
  
    #Initiate Water
    water = wm()
    water.ip = "192.168.1.77"
    water.polltime = 60

    #initiate Huqsvarna
    husqvarna = mower()
    husqvarna.hqAuth_url = 'https://api.authentication.husqvarnagroup.dev/v1/oauth2/token'
    husqvarna.hqurl = 'https://api.amc.husqvarna.dev/v1/mowers'
    husqvarna.hqCmdUrl = 'https://api.amc.husqvarna.dev/v1'
    husqvarna.hqapikey = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    husqvarna.hqauth = {
                        "client_id": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                        "client_secret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                        "grant_type": "client_credentials"
                        }    
                    
    #Validate Sessions
    charger1.validateSessions()    
    
    #Start all threads
    #heatpump()
    #asyncLoop()
    updAsync = threading.Thread(target=asyncLoop, args=(), name="AsyncLoop")
    updAsync.start()           
    #Husqvarna()
    updHusqvarna = threading.Thread(target=husqvarna.update, args=(), name="Husqvarna")
    updHusqvarna.start()      
    #pir()
    updPir = threading.Thread(target=pir, args=(), name="Pir")
    updPir.start()      
    #tibber()
    updTB = threading.Thread(target=tb.update, args=(), name="Tibber")
    updTB.start()     
    #water.update()
    updWater = threading.Thread(target=water.update, args=(), name="Water")
    updWater.start()           
    #charger1.update()    
    updChargeAmp = threading.Thread(target=charger1.update, args=(), name="ChargeAmp")
    updChargeAmp.start()        

    #shelly()
    updShPump = threading.Thread(target=sh_pump.update, args=(), name="ShellyPump")
    updShPump.start()        
    updShClorinator = threading.Thread(target=sh_clorinator.update, args=(), name="ShellyClorinator")
    updShClorinator.start()        
    #updShWorkshop = threading.Thread(target=sh_workshop.update, args=(), name="WorskhopSensor")
    #updShWorkshop.start()        

    updtc = threading.Thread(target=ThreadCleanup, args=(), name="ThreadCleanup")
    updtc.start()
    
    #TelldusLive()
    octoprint()
    init_log()
    logdata()
    Weather_Forecast()
    News()
            
    #Start Webserver
    app.run(host=IPADDRESS, threaded=True, port=IPPORT, debug=False)
    