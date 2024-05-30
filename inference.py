import pandas as pd
import numpy as np
from keras.utils import  img_to_array
from sklearn.preprocessing import LabelEncoder
from keras.models import load_model
import pydirectinput
import time
import pygetwindow as gw
import asyncio
import os
from mss.tools import to_png
from mss import mss
import keyboard
from PIL import Image
from datetime import datetime
from threading import Thread

# load model
model = load_model('car_driving_model.h5')
# load label encoder class  
label_encoder = LabelEncoder()
label_encoder.classes_ = np.load('classes.npy', allow_pickle=True)

UpState = True


def predict_action(image):
    image = np.expand_dims(image, axis=0)
    prediction = model.predict(image)
    predicted_class = label_encoder.inverse_transform([np.argmax(prediction)])
    # print(type(predicted_class[0]))
    return predicted_class[0]





imagePath = "images"
imgCount = 0
last_action = ""
key_log = []
pauseFlag = False

def cleanup():
    if os.path.exists(imagePath):
        os.rename(imagePath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.mkdir(imagePath)
    if os.path.exists("index.csv"):
        os.rename("index.csv", datetime.now().strftime('%Y-%m-%d_%H-%M-%S.csv'))
    with open("index.csv", "w") as f:
        f.write("image_name,last_action,action\n")

def keyPresss(k):
    if k == "left" or k == "right":
        print(f"pressing {k}")
        pydirectinput.keyDown(k)
        time.sleep(0.2)
        pydirectinput.keyUp(k)
    # else:
    #     print(f"pressing {k}")
    #     pydirectinput.keyDown(k)
    #     time.sleep(3)
    #     pydirectinput.keyUp(k)

def send_key(key):
    print(f"key: {key}")
    if str(key) == "nan" or str(key) == "None" or str(key) == "" or str(key) == " " or str(key) == "no_action":
        return
    key = str(key).split("+")
    if len(key) == 1:
        keyPresss(key[0])
    else:
        for k in key:
            Thread(target=keyPresss, args=(k,)).start()

def pressing_up():
    global pauseFlag
    while UpState:
        if not pauseFlag and gw.getActiveWindow().title == "Need for Speed™ Most Wanted" and UpState:
            # print("pressing upstarted")
            pydirectinput.keyDown("up")
        if pauseFlag or gw.getActiveWindow().title != "Need for Speed™ Most Wanted" and not UpState:
            # print("pressing up stopped")
            pydirectinput.keyUp("up")

        time.sleep(1)


async def data_gatherer(acw, sct):
    global imgCount, key_log, last_action
    left, top = acw.topleft
    right, bottom = acw.bottomright
    screenshot_path = f"{imagePath}/{imgCount}.png"
    screenshot = sct.grab({"left": left, "top": top, "width": right-left, "height": bottom-top})
    image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    image= image.resize((256, 144))
    key = predict_action(img_to_array(image) / 255.0)
    # to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
    # key_log.append(f"{imgCount}.png,{last_action},{key}\n")
    last_action = key
    # send key to the game
    send_key(key)
    
    imgCount += 1
    if len(key_log) >= 100:
        with open("index.csv", "a") as f:
            f.writelines(key_log)
        key_log = []

async def monitor_game():
    global pauseFlag, UpState
    upThread= Thread(target=pressing_up)
    # cleanup()
    try:
        upThread.start()
        with mss() as sct:
            while True:
                if keyboard.is_pressed('f3'):
                    print("exiting")
                    break
                elif keyboard.is_pressed('f2'):
                    pauseFlag = not pauseFlag
                    if pauseFlag:
                        print("pausing")
                        await asyncio.sleep(1)
                    else:
                        print("resuming")
                        await asyncio.sleep(1)
                if pauseFlag:
                    await asyncio.sleep(1)
                    continue
                active_window = gw.getActiveWindow()
                if active_window and active_window.title == "Need for Speed™ Most Wanted":
                    await data_gatherer(active_window, sct)
                else:
                    print("waiting for the game to be active")
                    await asyncio.sleep(1)
    except Exception as e:
        print(e)
    finally:
            if key_log:
                with open("index.csv", "a") as f:
                    f.writelines(key_log)
            pauseFlag = True
            UpState = False
            upThread.join()
            pydirectinput.keyUp("up")
            print("Completed Shutdown")




if __name__ == "__main__":
    asyncio.run(monitor_game())
    # cleanup()


