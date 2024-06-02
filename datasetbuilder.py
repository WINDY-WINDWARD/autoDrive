import pygetwindow as gw
import asyncio
import os
from mss.tools import to_png
from mss import mss
import keyboard
from PIL import Image
from datetime import datetime
import cv2
import numpy as np

imageSize = (256,144)
imgCount = 0
key_log = []
pauseFlag = True
last_action = "None"

uniqueID = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
imagePath = uniqueID
indexPath = f"{imagePath}.csv"

def cleanup():
    if os.path.exists(imagePath):
        os.rename(imagePath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.mkdir(imagePath)
    if os.path.exists(indexPath):
        os.rename(indexPath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S.csv'))
    with open(indexPath, "w") as f:
        f.write("image_name,last_action,action\n")

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
    return actions


async def data_gatherer(acw, sct):
    global imgCount, key_log, last_action, runcount
    runcount += 1
    left, top = acw.topleft
    right, bottom = acw.bottomright
    key = get_key_stroke()
    screenshot_path = f"{imagePath}/{imgCount}_{uniqueID}.png"
    screenshot = sct.grab({"left": left, "top": top, "width": right-left, "height": bottom-top})
    image= Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    image= image.resize(imageSize)
    image.save(screenshot_path)
    key_log.append(f"{imgCount}_{uniqueID}.png,{last_action},{key}\n")
    imgCount += 1
    last_action = key
    if len(key_log) >= 1000:
        with open(indexPath, "a") as f:
            f.writelines(key_log)
        key_log = []

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
    cleanup()
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
        print(e)
    finally:
            if key_log:
                with open(indexPath, "a") as f:
                    f.writelines(key_log)
            print(runcount)
            print("total time:" + str((current_time-startTime).total_seconds()/60) )

if __name__ == "__main__":
    asyncio.run(monitor_game())
