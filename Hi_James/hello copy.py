##HandTyperMain - Main Class for James's CV Project
##Author: Roel-Junior Alejo Viernes (001221190)
##Email: rv6049z@gre.ac.uk

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

import cv2
import tkinter as tk
import pynput
import time
from pymycobot import MyCobot280
import os

class HandTyper:
    
    def __init__(self, serial_port='/dev/ttyUSB0'):
        """
        Parameters for the mediapipe tasks
        """
        self.BaseOptions = mp.tasks.BaseOptions
        self.GestureRecognizer = mp.tasks.vision.GestureRecognizer
        self.GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        self.GestureRecognizerResult = mp.tasks.vision.GestureRecognizerResult
        self.VisionRunningMode = mp.tasks.vision.RunningMode
        
        self.james = MyCobot280(serial_port, 1000000) # Initialize the MyCobot280 with the serial port and baud rate

        """
        Flags for each mode
        """
        self.result_gesture = None
        self.key_mode = True

        """
        dir for the task file (The Model)
        """
        self.model_path = "Hand_Data_V7/gesture_recognizer.task"
        self.options = self.GestureRecognizerOptions(
            base_options=self.BaseOptions(model_asset_path=self.model_path),
            running_mode=self.VisionRunningMode.LIVE_STREAM,
            result_callback=self.print_result
        )

        """
        MediaPipe Hands for hand tracking
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

    def print_result(self, result, output_image: mp.Image, timestamp_ms: int):
        
        """
        Def: Callback function to handle the result of the gesture recognition.
        
        Params: 
        - result: The result of the gesture recognition.
        - output_image: The image with the recognized gestures drawn on it.
        - timestamp_ms: The timestamp of the image in milliseconds.
        """
        
        if result.gestures:
            
            if self.key_mode:
                print(f"Recognized gestures: {result.gestures}") #Only prints out the recognized gesture when key_mode is true
                
            target = str(result.gestures[0][0].category_name)

            if target and target != 'none':
                self.result_gesture = target
                
                self.translate(self.result_gesture)
            else:
                self.result_gesture = "No gesture detected"

    def draw_menu(self, frame):
        
        """
        Def: Draws the menu on the frame.
        Params: frame - The frame to draw the menu on.
        """
        cv2.putText(frame, "Menu: [Q] Quit) ", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, self.result_gesture, (10, 70), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2) 
        cv2.putText(frame, "Mouse Mode" if self.mouse_mode else "Key Mode", (10, 100), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2) # Display the current mode on the screen
        
    def main_capture(self):
        """
        Def: Main function to capture the video stream and process the hand gestures.
        """
        if not os.environ.get('DISPLAY'):
            raise RuntimeError('No DISPLAY environment variable set. OpenCV GUI features require a graphical environment.')
        cv2.namedWindow('HandTyperv1', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('HandTyperv1', self.windowsize()[0], self.windowsize()[1])
        cv2.setWindowProperty('HandTyperv1', cv2.WND_PROP_TOPMOST, 1)
        #cv2.moveWindow('HandTyperv1', (self.windowsize()[0] * 4 - self.windowsize()[0]), (self.windowsize()[1] * 4 - self.windowsize()[1])) # Moves the window to the top left corner of the screen
        
        frame_count = 0 # Frame counter for the webcam

        with self.GestureRecognizer.create_from_options(self.options) as recognizer: # Intialize the recognizer with the predefined options
            with self.mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence = 0.4) as hands: # Initialize the MediaPipe Hands module
                cap0 = cv2.VideoCapture(0) # Camera 0 for processing
                cap1 = cv2.VideoCapture(1) # Camera 1 for display
                if not cap0.isOpened() or not cap1.isOpened():
                    raise RuntimeError('Could not open both camera 0 and camera 1.')
                while True:
                    # Read from both cameras
                    ret0, frame0 = cap0.read()
                    ret1, frame1 = cap1.read()
                    if not ret0 or not ret1:
                        continue
                    frame_count += 1
                    if frame_count % 4 != 0:
                        continue
                    # Process frame from camera 0
                    frame0 = cv2.flip(frame0, 1)
                    rgb_frame = cv2.cvtColor(frame0, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    frame_timestamp_ms = int(time.time() * 1000)
                    recognizer.recognize_async(mp_image, frame_timestamp_ms)
                    results = hands.process(rgb_frame)
                    if results.multi_hand_landmarks:
                        if self.mouse_mode:
                            hand_landmarks = results.multi_hand_landmarks[0]
                        for hand_landmarks in results.multi_hand_landmarks:
                            self.mp_drawing.draw_landmarks(frame0, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    # Draw menu on frame1 (display frame)
                    self.draw_menu(frame1)
                    cv2.imshow('HandTyperv1', frame1)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break
                cap0.release()
                cap1.release()
                cv2.destroyAllWindows()

    def windowsize(self):
        
        """
        Def: Get the size of the window.
        Returns: A tuple with the width and height of the window.
        """
        if not os.environ.get('DISPLAY'):
            raise RuntimeError('No DISPLAY environment variable set. GUI features require a graphical environment.')
        main = tk.Tk()
        main.withdraw()  # Hide the main window
        width = main.winfo_screenwidth() // 4
        height = main.winfo_screenheight() // 4
        main.destroy()
        return width, height
    
    def james_dance(self):
        """
        Def: Makes the MyCobot280 dance.
        
        Todo: Add Gripper Control
        """
        self.james.set_color(255, 0, 0)
        self.james.move_to(0, 0, 0, 100, 100, 100)
        self.james.set_color(0, 255, 0)
        self.james.move_to(100, 100, 100, 100, 100, 100)
        self.james.set_color(0, 0, 255)
        self.james.move_to(-100, -100, -100, 100, 100, 100)
        
    def james_wave(self):
        """
        Def: Makes the MyCobot Wave via Axis 3
        """
        self.james.set_color(255, 0, 0)
        self.james.move_to(0, 0, 0, 100, 100, 100)
        self.james.set_color(0, 255, 0)
        self.james.move_to(0, 100, 0, 100, 100, 100)
        self.james.set_color(0, 0, 255)
        self.james.move_to(0, -100, 0, 100, 100, 100)
        
        
        
        
    def translate(self, sign):
        
        """
        Def: Translate the recognized gesture into a keyboard or mouse action.
        
        """
        
        keyboard = pynput.keyboard.Controller()
        target = sign.split()


        if target == 'BACKSPACE':
            keyboard.press(pynput.keyboard.Key.backspace)
            keyboard.release(pynput.keyboard.Key.backspace)
            
        elif target == 'ENTER':
            keyboard.press(pynput.keyboard.Key.space)
            keyboard.release(pynput.keyboard.Key.space)
            
        elif target == '1':
            keyboard.press(pynput.keyboard.Key.enter)
            keyboard.release(pynput.keyboard.Key.enter)

            
        elif target == '2':
            keyboard.press(pynput.keyboard.KeyCode.from_char('1'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('1'))
            keyboard.press(pynput.keyboard.KeyCode.from_char('0'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('0'))
            
        elif target == '2':
            keyboard.press(pynput.keyboard.KeyCode.from_char('1'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('1'))
            keyboard.press(pynput.keyboard.KeyCode.from_char('0'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('0'))
            
        elif target == '3':
            keyboard.press(pynput.keyboard.KeyCode.from_char('2'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('2'))
            keyboard.press(pynput.keyboard.KeyCode.from_char('0'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('0'))
            
        elif target == '0':
            keyboard.press(pynput.keyboard.KeyCode.from_char('3'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('3'))
            keyboard.press(pynput.keyboard.KeyCode.from_char('0'))
            keyboard.release(pynput.keyboard.KeyCode.from_char('0'))
                
        else:
            key_target = target[-1].strip()
            keyboard.press(key_target)
            
        print(f"Typed: {target[-1]}")


# Ubuntu/Linux dependency note
# To run this code on Ubuntu, ensure you have the following packages installed:
# sudo apt-get install python3-opencv python3-tk
# pip install mediapipe pynput pymycobot

if __name__ == '__main__':
    # You can specify the serial port if different from default
    hand_typer = HandTyper(serial_port='/dev/ttyUSB0')
    hand_typer.main_capture()
