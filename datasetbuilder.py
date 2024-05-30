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


imagePath = "images"
indexPath = "index.csv"
imageSize = (256,144)
imgCount = 0
key_log = []
pauseFlag = True
last_action = "None"

def cleanup():
    if os.path.exists(imagePath):
        os.rename(imagePath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.mkdir(imagePath)
    if os.path.exists(indexPath):
        os.rename(indexPath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S.csv'))
    with open(indexPath, "w") as f:
        f.write("image_name,last_action,action\n")

def get_key_stroke():
    actions =""
    if keyboard.is_pressed('up'):
        actions+="up+"
    if keyboard.is_pressed('down'):
        actions+="down+"
    if keyboard.is_pressed('left'):
        actions+= "left+"
    if keyboard.is_pressed('right'):
        actions+= "right+"
    return actions

def getROI(image):
    height = image.shape[0]
    width = image.shape[1]
    # Defining Triangular ROI: The values will change as per your camera mounts
    triangle = np.array([[(50, height-20), (width-50, height-20), (width-115, 60), (115, 60)]])
    # creating black image same as that of input image
    black_image = np.zeros_like(image)
    # Put the Triangular shape on top of our Black image to create a mask
    mask = cv2.fillPoly(black_image, triangle, 255)
    # applying mask on original image
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image

def canyEdgeDetector(image, threshold1, threshold2):
    edged = cv2.Canny(image, threshold1, threshold2)
    return edged

def gaussianBlur(image):
    return cv2.GaussianBlur(image, (5, 5), 0)

def getLines(image, original_image):
    lines = cv2.HoughLinesP(image,rho= 1,theta= np.pi/180,threshold= 30, minLineLength=20, maxLineGap=500)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(original_image, (x1, y1), (x2, y2), (0, 255, 0), 5)
    return original_image

def process_live(img):
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img = gaussianBlur(img)
    img = canyEdgeDetector(img, 41, 150)
    img = getROI(img)
    return Image.fromarray(img)


async def data_gatherer(acw, sct):
    global imgCount, key_log, last_action
    left, top = acw.topleft
    right, bottom = acw.bottomright
    key = get_key_stroke()
    screenshot_path = f"{imagePath}/{imgCount}.png"
    screenshot = sct.grab({"left": left, "top": top, "width": right-left, "height": bottom-top})
    image = cv2.resize(np.array(screenshot), imageSize)
    image = process_live(image)
    image.save(screenshot_path)
    key_log.append(f"{imgCount}.png,{last_action},{key}\n")
    imgCount += 1
    last_action = key
    if len(key_log) >= 100:
        with open(indexPath, "a") as f:
            f.writelines(key_log)
        key_log = []

async def monitor_game():
    global pauseFlag
    cleanup()
    try:
        with mss() as sct:
            while True:
                if keyboard.is_pressed('f3'):
                    print("exiting")
                    break
                elif keyboard.is_pressed('f2'):
                    pauseFlag = not pauseFlag
                    if pauseFlag:
                        print("pausing")
                    else:
                        print("resuming")
                if pauseFlag:
                    await asyncio.sleep(0.5)
                    continue
                active_window = gw.getActiveWindow()
                if active_window and active_window.title == "Need for Speed™ Most Wanted":
                    await data_gatherer(active_window, sct)
                else:
                    print("waiting for the game to be active")
                    await asyncio.sleep(1)
                await asyncio.sleep(0.1)
    except Exception as e:
        print(e)
    finally:
            if key_log:
                with open(indexPath, "a") as f:
                    f.writelines(key_log)

if __name__ == "__main__":
    asyncio.run(monitor_game())
