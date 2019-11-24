#!/usr/bin/env python
# encoding: utf-8

# LOGGER
LOGGER = True


def printlog(text):
    if LOGGER:
        print(text)


# -----------------------Watering Program---------------------#
import threading
import ctypes
import time

# Libraries for Running Motors
from MotorShield import PiMotor
import RPi.GPIO as GPIO

# Name of all the individual motors
m1 = PiMotor.Motor("MOTOR1", 1)
m2 = PiMotor.Motor("MOTOR2", 1)
m3 = PiMotor.Motor("MOTOR3", 1)
m4 = PiMotor.Motor("MOTOR4", 1)
motors = (m1, m2, m3, m4)

# Setting Up Sensors
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

p_sensors = (Input_P1Sensor, Input_P2Sensor, Input_P3Sensor, Input_P4Sensor)

# Default Status of Water System
status_of_plant1 = "Not Watering"
status_of_plant2 = "Not Watering"
status_of_plant3 = "Not Watering"
status_of_plant4 = "Not Watering"
status_of_tank = "Unknown"

# Thread for running Water System
class thread_with_exception(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        try:
            if self.name == "Manual_Watering":
                printlog("Watering Manually")
                for counter, m in enumerate(motors, 1):
                    update_status(counter, "Watering")
                    m.forward(100)
                    time.sleep(1.5)
                    m.stop()
                    update_status(counter, "Not Watering")

            elif self.name == "Auto_Watering":
                printlog("Watering Automatically")
                while True:
                    for counter, p_sensor in enumerate(p_sensors, 1):
                        if GPIO.input(p_sensor):
                            printlog("Watering Plant:" + str(counter))
                            update_status(counter, "Watering")
                            motors[counter - 1].forward(100)
                        else:
                            printlog("Not Watering Plant:" + str(counter))
                            update_status(counter, "Not Watering")
                            motors[counter - 1].stop()

                    if GPIO.input(Input_TSensor):
                        printlog("Tank is Empty. Adding water.")
                        update_status(5, "Empty")

                    else:
                        printlog("Tank Full")
                        update_status(5, "Full")

                    # Sleeps for one second before looping again
                    time.sleep(1)
        finally:

            printlog("Thread ended")

    def get_id(self):
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        # Stops motors once exception is raised
        for m in motors:
            m.stop()
        update_status(0)

        # Stops thread
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(SystemExit)
        )
        if res > 1 or res < 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            raise Exception("Failed to raise an exception and stop thread")


# Defining Water System Threads
t1 = thread_with_exception("Auto_Watering")
t2 = thread_with_exception("Manual_Watering")

# Var for buttons
AW_status = "OFF"
MW_status = "OFF"


def update_status(item, status="None"):
    global status_of_plant1
    global status_of_plant2
    global status_of_plant3
    global status_of_plant4
    global status_of_tank
    global MW_status
    global AW_status
    if item == 1:
        if status_of_plant1 != status:
            status_of_plant1 = status
        else:
            return
    elif item == 2:
        if status_of_plant2 != status:
            status_of_plant2 = status
        else:
            return
    elif item == 3:
        if status_of_plant3 != status:
            status_of_plant3 = status
        else:
            return
    elif item == 4:
        if status_of_plant4 != status:
            status_of_plant4 = status
        else:
            return
    elif item == 5:
        if status_of_tank != status:
            status_of_tank = status
        else:
            return
    elif item == 0:
        status_of_plant1 = "Not Watering"
        status_of_plant2 = "Not Watering"
        status_of_plant3 = "Not Watering"
        status_of_plant4 = "Not Watering"
        status_of_tank = "Full"
    elif item == 100:
        MW_status = "OFF"
    elif item == 101:
        MW_status = "ON"
    elif item == 102:
        AW_status = "OFF"
    elif item == 103:
        AW_status = "ON"

    socketio.emit("StatusUpdate", get_data())


def buttons_func(data):
    global AW_status
    global MW_status
    global t1
    global t2
    status = "Success"

    # Accepts data from user and decodes it
    msg = data['data']

    if msg == "auto_checked":
        update_status(103)
        try:
            t2.raise_exception()
            t2.join()
            t2 = thread_with_exception("Manual_Watering")
        finally:
            t1.start()
        # printlog("Starting Auto")

    elif msg == "auto_unchecked":
        update_status(102)
        t1.raise_exception()
        t1.join()
        printlog("Not Running Auto")
        # Resetting Thread
        t1 = thread_with_exception("Auto_Watering")

    elif msg == "manual_checked":
        update_status(101)

        # Checks is Auto is Running
        try:
            t1.raise_exception()
            t1.join()
            update_status(102)
            t1 = thread_with_exception("Auto_Watering")
            t2.start()
            t2.join()
            update_status(100)
            t2 = thread_with_exception("Manual_Watering")
            t1.start()
            update_status(103)

        except:
            printlog("Check: Auto_Watering Not Running")
            t2.start()
            t2.join()
            t2 = thread_with_exception("Manual_Watering")
            update_status(100)

    elif msg == "manual_unchecked":
        update_status(100)
        try:
            t2.raise_exception()
            t2 = thread_with_exception("Manual_Watering")
        except:
            printlog("Manual Not Running")

    else:
        status = "Cannot read data"

    return jsonify({"status": status})


# ----------------------------------------------------------------------------------#

# Server-Code
import datetime, json

# Getting Data for website
def get_data():
    time = datetime.datetime.now()
    dt_string = time.strftime('%d/%m/%y %I:%M %S %p')
    return {
        "last_updated":dt_string,
        "Plant1":status_of_plant1,
        "Plant2":status_of_plant2,
        "Plant3":status_of_plant3,
        "Plant4":status_of_plant4,
        "Tank":status_of_tank,
        "AW":AW_status,
        "MW":MW_status}  


# Starting Flask Application
from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    url_for,
    send_from_directory,
)
from flask_socketio import SocketIO, emit

PORT = 443
app = Flask(__name__)
socketio = SocketIO(app, async_mode=None, logger=False, engineio_logger=False)


@app.route("/")
@app.route("/home")
def home():
    # Main Site
    return render_template("home.html")

@socketio.on("connect")
def connect():
    print("A Client has connected")
    emit("Response", {"data": "Connected!"})
    emit("StatusUpdate", get_data())


@socketio.on("disconnect")
def test_disconnect():
    print("Client disconnected")
    
@socketio.on('client')
def handle_request(msg):
    print("Recieved MSG from client")
    #print(msg)
    return buttons_func(msg)  


if __name__ == "__main__":
    try:
        socketio.run(app, port =PORT)
    finally:
        printlog("Cleaning Up Pins")
        GPIO.cleanup()


# Include:write date to file to make graph/adding checks for thread before starting thread in auto func

"""
@app.route("/data", method=["GET"])
def data():
    return jsonisfy(get_data())


@app.route("/updatestatus")
def updatestatus():
    ws = request.environ("wsgi.websocket")
    if not ws:
        raise RuntimeError("Environment lacks WSGI WebSocket support")
    if ws:
        print("Hello")


http_server = WSGIServer(("", PORT), app, handler_class=WebSocketHandler)
http_server.serve_forever()
"""

