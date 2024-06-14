import pygetwindow as gw
import asyncio
import os
from mss.tools import to_png
from mss import mss
import keyboard
from datetime import datetime
import cv2
import numpy as np
import pandas as pd

imageSize = (256,144)
key_log = []
img_log = []
pauseFlag = True
last_action = "None"
uniqueID = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')


def saveDataframe():
    global key_log, img_log, uniqueID
    # convert the logs to numpy arrays
    key_log = np.array(key_log)
    img_log = np.array(img_log)
    print("saving data")
    np.save(f"key_log_{uniqueID}.npy", key_log)
    np.save(f"img_log_{uniqueID}.npy", img_log)


# def get_key_stroke():
#     actions =""
#     if keyboard.is_pressed('up'):
#         actions+="up+"
#     if keyboard.is_pressed('down'):
#         actions+="down+"
#     if keyboard.is_pressed('left'):
#         actions+= "left+"
#     if keyboard.is_pressed('right'):
#         actions+= "right+"
#     return actions


def encode_action(action):
    mapping = {'up': 0, 'left': 1, 'right': 2, 'down': 3}
    if action == "None":
        return np.zeros(4)
    ac = mapping[action]
    temp=np.zeros(4)
    temp[ac]=1
    return temp

def get_key_stroke():
    actions = ""
    if keyboard.is_pressed('up'):
        actions = "up"
    elif keyboard.is_pressed('down'):
        actions = "down"
    elif keyboard.is_pressed('left'):
        actions = "left"
    elif keyboard.is_pressed('right'):
        actions = "right"
    else:
        actions = "None"
    actions = encode_action(actions)
    return actions


async def data_gatherer(acw, sct):
    global key_log, img_log, runcount
    runcount += 1
    left, top = acw.topleft
    right, bottom = acw.bottomright
    key = get_key_stroke()
    screenshot = sct.grab({"left": left, "top": top, "width": right-left, "height": bottom-top})
    # convert screenshot to cv2 image
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, imageSize)
    img_log.append(img)
    key_log.append(key)
    # save the data every 1000 frames
    # if runcount % 1000 == 0:
    #     saveDataframe()

def fpsCounter():
    global runcount,startTime,current_time
    current_time = datetime.now()
    elapsed = (current_time-startTime).total_seconds()
    fps = runcount / elapsed
    fps = round(fps,2)
    print(f"FPS: {fps}")

runcount = 0
startTime = datetime.now()
current_time = datetime.now()
async def monitor_game():
    global pauseFlag, runcount,current_time
    # cleanup()
    try:
        with mss() as sct:
            while True:
                if runcount % 1000 == 0:
                    fpsCounter()
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
                    await asyncio.sleep(2)
                    continue
                active_window = gw.getActiveWindow()
                if active_window and active_window.title == "Need for Speed™ Most Wanted":
                    await data_gatherer(active_window, sct)
                else:
                    print("waiting for the game to be active")
                    await asyncio.sleep(1)
    except Exception as e:
        print ("Error")
        print(e)
    finally:
            saveDataframe()
            print(runcount)
            print("total time:" + str((current_time-startTime).total_seconds()/60) )

if __name__ == "__main__":
    asyncio.run(monitor_game())
