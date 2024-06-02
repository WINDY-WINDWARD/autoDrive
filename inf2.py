# %%
import pandas as pd
import numpy as np
from keras.utils import  img_to_array, load_img
from sklearn.preprocessing import LabelEncoder
from keras.models import load_model
import pydirectinput
import time
import pygetwindow as gw
# import asyncio
import os
# from mss.tools import to_png
from mss import mss
import keyboard
from PIL import Image
import cv2
from datetime import datetime
# from threading import Thread
import logging

logging.basicConfig(level=logging.DEBUG)

# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'



# %%
# load model
model = load_model('alexnet.h5')
logging.debug("model loaded")

UpState = True
mapping = { 0:'up',  1:'left',  2:'right',  3:'down'}


def predict_action(image):
    logging.debug("predicting action")
    image = np.expand_dims(image, axis=0)
    prediction = model.predict(image)
    return mapping[np.argmax(prediction)]



# %%
def getROI(image):
    logging.debug("getting ROI")
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
    logging.debug("applying canny edge detector")
    edged = cv2.Canny(image, threshold1, threshold2)
    return edged

def gaussianBlur(image):
    logging.debug("applying gaussian blur")
    return cv2.GaussianBlur(image, (5, 5), 0)


def process_live(img):
    logging.debug("processing live image")
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # img = gaussianBlur(img)
    # img = canyEdgeDetector(img, 41, 150)
    # img = getROI(img)
    logging.debug("image processed")
    return img






# %%
imagePath = "images"
imgCount = 0
last_action = ""
key_log = []
pauseFlag = False

def cleanup():
    logging.debug("cleaning up")
    if os.path.exists(imagePath):
        os.rename(imagePath, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.mkdir(imagePath)
    if os.path.exists("index.csv"):
        os.rename("index.csv", datetime.now().strftime('%Y-%m-%d_%H-%M-%S.csv'))
    with open("index.csv", "w") as f:
        f.write("image_name,last_action,action\n")

def keyPresss(k):
    logging.debug(f"pressing {k}")
    if k == "left" or k == "right":
        pydirectinput.keyDown(k)
        time.sleep(0.2)
        pydirectinput.keyUp(k)
    # else:
    #     print(f"pressing {k}")
    #     pydirectinput.keyDown(k)
    #     time.sleep(3)
    #     pydirectinput.keyUp(k)

def send_key(key):
    logging.debug(f"sending key {key}")
    if key == "left":
        pressing_left()
    elif key == "right":
        pressing_right()
    elif key == "up":
        pressing_up()
    else:
        logging.debug("no key pressed")
        pydirectinput.keyUp("up")
        pydirectinput.keyUp("left")
        pydirectinput.keyUp("right")

def pressing_up():
    logging.debug("pressing up")
    pydirectinput.keyDown("up")
    pydirectinput.keyUp("left")
    pydirectinput.keyUp("right")

def pressing_left():
    logging.debug("pressing left")
    pydirectinput.keyDown("left")
    # pydirectinput.keyUp("up")
    pydirectinput.keyUp("right")

def pressing_right():
    logging.debug("pressing right")
    pydirectinput.keyDown("right")
    # pydirectinput.keyUp("up")
    pydirectinput.keyUp("left")

imageSize = (256,144)


def data_gatherer(acw, sct):
    logging.debug("gathering data")
    global imgCount, key_log, last_action
    left, top = acw.topleft
    right, bottom = acw.bottomright
    screenshot_path = f"{imagePath}/{imgCount}.png"
    screenshot = sct.grab({"left": left, "top": top, "width": right-left, "height": bottom-top})
    image = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    image = image.resize(imageSize)
    image = process_live(img_to_array(image))
    key = predict_action(image / 255.0)
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

def monitor_game():
    global pauseFlag, UpState
    # cleanup()
    try:
        with mss() as sct:
            while True:
                logging.debug("Starting the loop")
                if keyboard.is_pressed('f3'):
                    print("exiting")
                    break
                elif keyboard.is_pressed('f2'):
                    pauseFlag = not pauseFlag
                    if pauseFlag:
                        print("pausing")
                        time.sleep(1)
                    else:
                        print("resuming")
                        time.sleep(1)
                if pauseFlag:
                    time.sleep(1)
                    continue
                active_window = gw.getActiveWindow()
                if active_window and active_window.title == "Need for Speed™ Most Wanted":
                    data_gatherer(active_window, sct)
                else:
                    print("waiting for the game to be active")
                    time.sleep(1)
    except Exception as e:
        print(e)
    finally:
            pauseFlag = True
            UpState = False
            pydirectinput.keyUp("up")
            pydirectinput.keyUp("left")
            pydirectinput.keyUp("right")
            pydirectinput.keyUp("down")
            print("Completed Shutdown")


if __name__ == "__main__":
    monitor_game()


