#!/usr/bin/env python
# encoding: utf-8
import threading
import ctypes
import time

#Libraries for Running Motors
from MotorShield import PiMotor
import RPi.GPIO as GPIO

#Name of all the individual motors
m1 = PiMotor.Motor("MOTOR1", 1)
m2 = PiMotor.Motor("MOTOR2", 1)
m3 = PiMotor.Motor("MOTOR3", 1)
m4 = PiMotor.Motor("MOTOR4", 1)
motors = (m1,m2,m3,m4)

#Setting Up Sensors
GPIO.setmode(GPIO.BOARD)
Input_P1Sensor = 35
Output_P1Sensor = 37

Input_P2Sensor = 29
Output_P2Sensor = 33

Input_P3Sensor = 7
Output_P3Sensor = 5

Input_P4Sensor = 8
Output_P4Sensor = 10

Input_TSensor = 36
Output_TSensor = 38

GPIO.setup(Input_P1Sensor, GPIO.IN)
GPIO.setup(Output_P1Sensor, GPIO.OUT)
GPIO.output(Output_P1Sensor, GPIO.HIGH)

GPIO.setup(Input_P2Sensor, GPIO.IN)
GPIO.setup(Output_P2Sensor, GPIO.OUT)
GPIO.output(Output_P2Sensor, GPIO.HIGH)

GPIO.setup(Input_P3Sensor, GPIO.IN)
GPIO.setup(Output_P3Sensor, GPIO.OUT)
GPIO.output(Output_P3Sensor, GPIO.HIGH)

GPIO.setup(Input_P4Sensor, GPIO.IN)
GPIO.setup(Output_P4Sensor, GPIO.OUT)
GPIO.output(Output_P4Sensor, GPIO.HIGH) 

GPIO.setup(Input_TSensor, GPIO.IN)
GPIO.setup(Output_TSensor, GPIO.OUT)
GPIO.output(Output_TSensor, GPIO.HIGH) 

p_sensors = (Input_P1Sensor,Input_P2Sensor,Input_P3Sensor,Input_P4Sensor)

#Default Status of Water System
status_of_plants = ["Not Watering","Not Watering","Not Watering","Not Watering"]
status_of_tank = "Full"

#Thread for running Water System
class thread_with_exception(threading.Thread):
    
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    
    def run(self):
        global status_of_plants
        global status_of_tank
        try:
            if self.name == "Manual_Watering":
                print("Watering Manually")
                i = 0
                for m in motors:
                    status_of_plants[i] = "Watering"
                    m.forward(100)
                    time.sleep(1.5)
                    m.stop()
                    status_of_plants[i] = "Not Watering"
                    i += 1
                
            elif self.name == "Auto_Watering":
                print("Watering Automatically")
                while True:
                    m = 0
                    for p_sensor in p_sensors:
                        if GPIO.input(p_sensor):
                            print("Watering Plant:", m+1)
                            status_of_plants[m] = 'Watering'
                            motors[m].forward(100)
                        else:
                            print("Not Watering Plant:",m+1)
                            status_of_plants[m] = 'Not Watering'
                            motors[m].stop()
                        m += 1

                    if GPIO.input(Input_TSensor):
                        print("Tank is Empty. Adding water.")
                        status_of_tank = 'Empty'

                    else:
                        print("Tank Full")
                        status_of_tank = 'Full'
                    
                    #Sleeps for one second before looping again
                    time.sleep(1)
        finally:
            
            print("Thread ended")
            
    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
        
    def raise_exception(self):
        global status_of_plants
        #Stops motors once exception is raised
        for m in motors:
            m.stop()
        status_of_plants = "Not Watering"
        
        #Stops thread
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                     ctypes.py_object(SystemExit))
        if res > 1 or res < 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            raise Exception('Failed to raise an exception and stop thread')

#Defining Water system threads
t1  = thread_with_exception('Auto_Watering')
t2 = thread_with_exception('Manual_Watering')
#----------------------------------------------------------------------------------

#LOGGER
LOGGER = True
def printlog(text):
    if(LOGGER):
        print(text)

#Server-Code
import datetime, json

#Var for buttons
TAW_status = ""
MW_status = ""

#Getting Info for website
def get_info():
    template = {
        "last_updated": datetime.datetime.now(),
        "Plant1": status_of_plants[0],
        "Plant2": status_of_plants[1],
        "Plant3": status_of_plants[2],
        "Plant4": status_of_plants[3],
        "Tank": status_of_tank,
        #For Buttons
        "TAW": TAW_status,
        "MW": MW_status,
    }
    return template

# Starting Flask Application
from flask import Flask, render_template, request, url_for

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    pi_info = get_info()
    return render_template("home.html", pi_info=pi_info)

@app.route("/auto", methods=["POST"])
def auto():
    global TAW_status
    global MW_status
    global t1
    global t2
    status = "Success"
    
    #Accepts data from user and decodes it
    data = request.get_data().decode("utf-8")
    
    
    if data == "auto_checked":
        TAW_status = "checked"
        #Possible add a check in a future version
        t1.start()
        printlog("Starting Auto")
    elif data == "auto_unchecked":
        TAW_status = ""
        t1.raise_exception()
        t1.join()
        printlog("Not Running Auto")
        t1 = thread_with_exception('Auto_Watering')
    elif data == "manual_checked":
        MW_status = "checked"
        try:
            t1.raise_exception()
            t2.start()
            t2.join()
            t1  = thread_with_exception('Auto_Watering')
            t1.start()
        except:
            print("Check:Auto_Watering Not Running")
            t2  = thread_with_exception('Manual_Watering')
            t2.start()
        MW_status = ""
    elif data == "manual_unchecked":
        MW_status = ""
    else:
        status = "Cannot read data"
    return json.dumps({"status": status})


if __name__ == "__main__":
    try:
        app.run(debug=True, host="0.0.0.0")
    finally:
        printlog("Cleaning Up Pins")
        GPIO.cleanup()
        
# Include:write date to file to make graph/fix watering status with autoloop
