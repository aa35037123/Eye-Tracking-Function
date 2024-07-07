import cv2
import os
import dlib
import numpy as np
from math import hypot
from imutils import face_utils
from utils import *
from functions import *
# import winsound

def play_sound(sound_file):
    os.system(f"aplay {sound_file}")

def search_function():
    print("Search function triggered")

def send_message_function():
    print("Send message function triggered")

def play_music_function():
    print("Play music function triggered")

# KEYBOARD SETTING/VARIABLES: 
keyboard = np.zeros((350, 800, 3), np.uint8)  # Increased height to add buttons
first_col_index = [0, 10, 20, 30, 40, 50, 60]
second_col_index = [1, 11, 21, 31, 41, 51, 61]
third_col_index = [2, 12, 22, 32, 42, 52, 62]
fourth_col_index = [3, 13, 23, 33, 43, 53, 63]
fifth_col_index = [4, 14, 24, 34, 44, 54, 64]
sixth_col_index = [5, 15, 25, 35, 45, 55, 65]
seventh_col_index = [6, 16, 26, 36, 46, 56, 66]
eighth_col_index = [7, 17, 27, 37, 47, 57, 67]
ninth_col_index = [8, 18, 28, 38, 48, 58, 68]
tenth_col_index = [9, 19, 29, 39, 49, 59, 69]
# button_col_index = [60, 61, 62]  # New buttons
key_set = {0: "1", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "7", 7: "8", 8: "9", 9: "0",
           10: "q", 11: "w", 12: "e", 13: "r", 14: "t", 15: "y", 16: "u", 17: "i", 18: "o", 19: "p",
           20: "a", 21: "s", 22: "d", 23: "f", 24: "g", 25: "h", 26: "j", 27: "k", 28: "l", 29: ";",
           30: "z", 31: "x", 32: "c", 33: "v", 34: "b", 35: "n", 36: "m", 37: "<", 38: ">", 39: "?",
           40: "+", 41: "-", 42: ",", 43: ".", 44: "/", 45: "*", 46: "@", 47: " ", 48: "!", 49: "<-",
           50: "%", 51: "$", 52: ":", 53: "&", 54: "(", 55: ")", 56: "=", 57: "_", 58: "'", 59: "#",
           60: "web", 61: "msg", 62: "music"}  # New buttons

# Counters
frame_count_column = 0  # this is frame count for column
frame_count_row = 0  # this is frame count for row
col_index = []
col = 0
column_previous = 0
blink_count = 0  # this for counting the blink (used for blink for changing the row and column)
blink_count_indivisual_key = 0  # this is for counting the blink to check whether the key should press or not
font_letter = cv2.FONT_HERSHEY_PLAIN
col_select = False  # this for selecting the particular column
row = 0  # this is to count the row after particular column is selected
IMG_SIZE = (34, 26)
IMG_SIZE_GAZE = (64, 56)
###################
type_text = ""  # this is to store the typed character
###################

# COUNTER FOR GAZE DETECTION
gaze_right_frame_count = 0
gaze_left_frame_count = 0

# user defined class object for blink detection using cnn model
bd = Blink_detection()

# user defined class for gaze detection
gd = Gaze_detection()

# class labels of gaze detection
gaze_class_labels = ['center', 'left', 'right']

white_board = np.ones((100, 800, 3), np.uint8)

#######################
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("FILES/shape_predictor_68_face_landmarks.dat")
cap = cv2.VideoCapture(0)
#####################
# FUNCTION TO DRAW KEYBOARD
def draw_keyboard(letter_index, letter, light):
    # if letter_index < 60:
    #     row, col = divmod(letter_index, 10)
    #     x = col * 80
    #     y = row * 50
    # else:
    #     x = col * 80
    #     y = row * 50
    #     y = 300  # Position for new buttons
        # if letter_index == 60:
            # x = 0
    #     elif letter_index == 61:
    #         x = 266
    #     elif letter_index == 62:
    #         x = 532

    row, col = divmod(letter_index, 10)
    x = col * 80
    y = row * 50
    
    font = cv2.FONT_HERSHEY_PLAIN
    letter_thickness = 2
    key_space = 2
    font_scale = 3
    height = 50
    width = 80
    if light:
        cv2.rectangle(keyboard, (x + key_space, y + key_space), (x + width - key_space, y + height - key_space), (0, 255, 0), -1)
    else:
        cv2.rectangle(keyboard, (x + key_space, y + key_space), (x + width - key_space, y + height - key_space), (0, 255, 0), key_space)
    letter_size = cv2.getTextSize(letter, font, font_scale, letter_thickness)[0]
    letter_height, letter_width = letter_size[1], letter_size[0]
    letter_x = int((width - letter_width) / 2) + x
    letter_y = int((height + letter_height) / 2) + y
    cv2.putText(keyboard, letter, (letter_x, letter_y), font, font_scale, (255, 255, 255), letter_thickness)

def handle_button_press(letter, text, crawler):
    if letter == "msg":
        telegram_bot_sendtext(text)
    elif letter == "web":
        crawler.do_crawling(text)
    elif letter == "music":
        play_music_function()

crawler = AutoCrawler()

while True:
    main_windows = np.zeros((780, 1000, 3), np.uint8)
    if col_select == True:
        frame_count_row = frame_count_row + 1
    if gaze_right_frame_count == 10:
        print("voluntary right gaze detected")
        # winsound.Beep(500,10)
        play_sound("FILES/beep-01a.wav")
        col = col + 1
        gaze_right_frame_count = 0
        if col == 10:
            col = 0
    if gaze_left_frame_count == 10:
        print("voluntary left gaze detected")
        # winsound.Beep(500,10)
        play_sound("FILES/beep-01a.wav")
        col = col - 1
        gaze_left_frame_count = 0
        if col == -1:
            col = 9

    if frame_count_row == 10:
        row = row + 1
        if row == 7:  # Updated to handle 7 rows now
            row = 0  # resetting the row
            col_select = False
        frame_count_row = 0
    if col == 0:
        col_index = first_col_index
    elif col == 1:
        col_index = second_col_index
    elif col == 2:
        col_index = third_col_index
    elif col == 3:
        col_index = fourth_col_index
    elif col == 4:
        col_index = fifth_col_index
    elif col == 5:
        col_index = sixth_col_index
    elif col == 6:
        col_index = seventh_col_index
    elif col == 7:
        col_index = eighth_col_index
    elif col == 8:
        col_index = ninth_col_index
    elif col == 9:
        col_index = tenth_col_index
    # elif col == 10:
    #     col_index = button_col_index  # New buttons

    keyboard[:] = (0, 0, 0)  # resetting the keyboard
    if col_select == False:
        for i in range(0, 63):
            if i in col_index:
                draw_keyboard(i, key_set[i], True)
            else:
                draw_keyboard(i, key_set[i], False)
    else:
        for i in range(0, 63):
            if i == col_index[row]:
                draw_keyboard(i, key_set[i], True)
            else:
                draw_keyboard(i, key_set[i], False)
    # Blink integration begin
    _, frame = cap.read()  # reading the frame form the webcam
    
    frame = cv2.flip(frame, flipCode=1 )
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # coverting the bgr frame to gray scale
    faces = detector(gray)  # this returns the dlib rectangle
    # now extracting the rectangle which contain the upper and lower cordinates of the face
    if len(faces) == 0:
        continue
    face = faces[0]
    shapes = predictor(gray, face)
    shapes = face_utils.shape_to_np(shapes)

    # EYE CROPING FOR BLINK
    eye_img_l, eye_rect_l = bd.crop_eye(gray, eye_points=shapes[36:42])
    eye_img_r, eye_rect_r = bd.crop_eye(gray, eye_points=shapes[42:48])

    # EYE CROPING FOR GAZE
    eye_img_l_g = gd.crop_eye(gray, eye_points=shapes[36:42])

    eye_img_l = cv2.resize(eye_img_l, dsize=IMG_SIZE)
    eye_img_r = cv2.resize(eye_img_r, dsize=IMG_SIZE)
    # eye_img_r = cv2.flip(eye_img_r, flipCode=1)

    # RESIZING THE CROPPED GAZE INPUT EYE
    eye_img_l_g = cv2.resize(eye_img_l_g, dsize=IMG_SIZE_GAZE)

    eye_input_l = eye_img_l.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
    eye_input_r = eye_img_r.copy().reshape((1, IMG_SIZE[1], IMG_SIZE[0], 1)).astype(np.float32) / 255.
    eye_input_l_g = eye_img_l_g.copy().reshape((1, IMG_SIZE_GAZE[1], IMG_SIZE_GAZE[0], 1)).astype(np.float32) / 255.

    pred_l, pred_r = bd.model_predict(eye_input_l, eye_input_r)
    gaze = gd.model_predict(eye_input_l_g)
    # print(gaze)
    if gaze == "right" and col_select == False and pred_l >= 0.3 and pred_r >= 0.3:
        print("right gaze")
        cv2.putText(main_windows, "--RIGHT--", (50, 325), font_letter, 2, (255, 255, 51), 2)
        cv2.putText(main_windows, "--RIGHT--", (800, 325), font_letter, 2, (255, 255, 51), 2)
        gaze_right_frame_count = gaze_right_frame_count + 1
    if gaze == "left" and col_select == False and pred_l >= 0.3 and pred_r >= 0.3:
        print("left gaze")
        cv2.putText(main_windows, "--LEFT--", (50, 325), font_letter, 2, (255, 255, 51), 2)
        cv2.putText(main_windows, "--LEFT--", (800, 325), font_letter, 2, (255, 255, 51), 2)

        gaze_left_frame_count = gaze_left_frame_count + 1
    if gaze == "center" and col_select == False:
        print("center gaze")
        cv2.putText(main_windows, "--CENTER--", (50, 325), font_letter, 2, (255, 255, 51), 2)
        cv2.putText(main_windows, "--CENTER--", (800, 325), font_letter, 2, (255, 255, 51), 2)

    if pred_l < 0.3 and pred_r < 0.3:
        print("blink detected")
        cv2.putText(main_windows, "------BLINK DETECTED------", (375, 325), font_letter, 1, (0, 0, 255), 2)
        
        blink_count = blink_count + 1
        if col_select == True:
            blink_count_indivisual_key = blink_count_indivisual_key + 1
            frame_count_row = frame_count_row - 1
        else:
            frame_count_column = frame_count_column - 1
    else:
        blink_count = 0
        blink_count_indivisual_key = 0
        
    if blink_count == 10:
        play_sound('FILES/beep-01a.wav')
        col_select = True
    # implementing keyboard typing
    if blink_count_indivisual_key == 10 and col_select == True:
        col_select = False  # to disable the active column
        selected_key = key_set[col_index[row]]
        print("typed text:", selected_key)
        if selected_key == '<-':
            type_text = type_text[:-1]
        elif selected_key in ["web", "msg", "music"]:
            # print('Press the special button')
            handle_button_press(selected_key, type_text, crawler)
        else:
            type_text = type_text + selected_key
        blink_count_indivisual_key = 0
        white_board[:] = (0, 0, 0)
        # winsound.Beep(500, 100)
        play_sound("FILES/beep-01a.wav")
        cv2.putText(white_board, type_text, (10, 50), cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 3)
        row = 0  # resetting the row

    # visualize
    state_l = 'O %.1f' if pred_l > 0.1 else '- %.1f'
    state_r = 'O %.1f' if pred_r > 0.1 else '- %.1f'

    state_l = state_l % pred_l
    state_r = state_r % pred_r

    cv2.rectangle(frame, pt1=tuple(eye_rect_l[0:2]), pt2=tuple(eye_rect_l[2:4]), color=(64, 224, 208), thickness=2)
    cv2.rectangle(frame, pt1=tuple(eye_rect_r[0:2]), pt2=tuple(eye_rect_r[2:4]), color=(255, 0, 0), thickness=2)

    # Combining all windows into single window:
    main_windows[50:150, 100:200] = cv2.resize(cv2.cvtColor(eye_img_l, cv2.COLOR_BGR2RGB), (100, 100))
    cv2.putText(main_windows, "CROPPED LEFT EYE", (90, 170), font_letter, 1, (255, 255, 51), 2)
    cv2.putText(main_windows, str(state_l + "%"), (100, 200), font_letter, 2, (0, 0, 255), 2)
    main_windows[50:150, 800:900] = cv2.resize(cv2.cvtColor(eye_img_r, cv2.COLOR_BGR2RGB), (100, 100))
    cv2.putText(main_windows, "CROPPED RIGHT EYE", (790, 170), font_letter, 1, (255, 255, 51), 2)
    cv2.putText(main_windows, str(state_r + "%"), (800, 200), font_letter, 2, (0, 0, 255), 2)

    main_windows[0:300, 300:700] = cv2.resize(frame, (400, 300))
    main_windows[350:700, 100:900] = keyboard  # Adjusted to fit the keyboard
    main_windows[670:770, 100:900] = white_board
    cv2.imshow("Main_Windows", main_windows)
    key = cv2.waitKey(10)
    if key == ord('q'):
        break
cv2.destroyAllWindows()
