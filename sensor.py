import sys
import time
import math
import smbus2
from typing import Tuple

sys.modules['smbus'] = smbus2

from mpu6050 import mpu6050

mpu = mpu6050(0x68) # defaults to 0b1101000 == 0x68

from flask import Flask, Response

app = Flask(__name__)

def celsius_to_farenheit(tc: float)-> float:
    """ Helper function to convert from C to F """
    return (tc * 1.8) + 32.0


def calculate_roll_and_pitch(x: float, y: float, z: float)-> Tuple[float, float]:
    """ Helper function to compute roll and pitch, respectively, from accel data.
        https://mwrona.com/posts/accel-roll-pitch/
    """
    try:
        return abs(math.degrees(math.atan2(y, z))), abs(math.degrees(math.asin(x/9.81)))
    except ValueError:
        return -1.0, -1.0

def kickstart_sensor():
    """ Convenience function to try and kickstart an error'd sensor """
    mpu.bus.write_byte_data(mpu.address, mpu.PWR_MGMT_1, 0x00)
    
@app.route("/status")
def get_status()-> Response:
    status = read_sensor()
    if status == -1:
        kickstart_sensor()
        status = read_sensor()

    if status == 0:
        return "Open\n", 200
    elif status == 1:
        return "Moving ...\n", 200
    elif status == 2:
        return "Closed\n", 200
    else:
        return "I/O Failure\n", 500


def read_sensor()-> int:
    # https://github.com/m-rtijn/mpu6050
    # accel is in m/s^2 unless you set g=True
    accel = mpu.get_accel_data()
    # gyro appears to be deg?
    # gyro = sensor.get_gyro_data()
    # temp is in celsius
    # temp = celsius_to_farenheit(sensor.get_temp())
            
    roll, pitch = calculate_roll_and_pitch(**accel)

    print(f"ROLL: {roll}")

    if 0 < roll < 10:
        return 0 # OPEN
    elif 11 < roll < 85 or 105 < roll < 180:
        return 1 # MOVING
    elif 85 < roll < 105:
        return 2 # CLOSED
    else:
        return -1 # ERROR


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, threaded=True)

