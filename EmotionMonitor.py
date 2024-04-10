import rumps
import cv2
import dlib
import numpy as np
import time
from collections import Counter
from ehg_nfeat24_B2_Hg1_D4_E1 import HourglassNet
import torch
import beepy

from gaze import find_landmarks, detect_face, crop_eye, process_eyes, process_gaze, tuple_from_dlib_shape
from emotion import EmotionDetector
from blink import BlinkDetector
from notification import Notification
from file_manager import FileManager

# Emotion Monitor Class
class EmotionMonitor:
    def __init__(self, notify = Notification()):
        self.start_time = time.time()
        self.blink_start_time = time.time()
        self.emotion_counts = Counter()
        self.emotion_duration = 10
        self.MIN_BLINK_THRESHOULD = 12
        self.MAX_BLINK_THRESHOULD = 15
        self.blink_duration = 10
        self.window_width = 300
        self.window_height = 200
        self.total_blinks = 0

        self.cap = None
        self.file_path = "FILES/ergo-sight-progress.txt"
        self.dominant_emotion = "Normal"
        
        self.blink = BlinkDetector()
        self.emotion = EmotionDetector ()
        self.file = FileManager()

        self.notify = notify

        # Load models and initialize constants
        self.predictor_path = 'shape_predictor_68_face_landmarks.dat'
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(self.predictor_path)

        # Load gaze model
        self.gaze_model = HourglassNet()
        self.gaze_model = torch.nn.DataParallel(self.gaze_model)
        checkpoint = torch.load('ehg_nfeat24_B2_Hg1_D4_E1.pth.tar', map_location='cpu')
        checkpoint['state_dict'] = {k:v for (k, v) in checkpoint['state_dict'].items() if k.split('_')[-1] != 'tracked'}  
        self.gaze_model.load_state_dict(checkpoint['state_dict'])

        self.last_frame_index = 0

        # Load Model
        print('==> Loading model')

        self._last_frame_index = 0
        self._indices = []
        self._frames = {}

    def send_notification(self, title, subtitle, message):
        rumps.notification(title = title, subtitle = subtitle, message = message, sound=True)

    def get_video_capture_device(self):
        # Check if cv2.VideoCapture(1) is available
        if cv2.VideoCapture(1).isOpened():
            return cv2.VideoCapture(1)
        else:
            return cv2.VideoCapture(0)         

    def start_monitoring(self):

        self.cap = self.get_video_capture_device()
        
        while self.cap.isOpened():

            ret, img = self.cap.read()

            if not ret:
                continue

            self.last_frame_index =+ 1
            self.current_index = self.last_frame_index
            
            # Operations on the frame come here
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            frame = {'frame_index': self.current_index,
                        'bgr': img,
                        'gray': gray,}

            self._frames[self.current_index] = frame
            self._indices.append(self.current_index)

            #Face Detector
            frame = detect_face(frame, self._indices, self._frames)
            if frame['faces'] == None:
                cv2.putText(frame['bgr'], 'No Face Detected', org=(20, 40), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1.00,
                            color=(0, 0, 255), thickness=1, lineType=cv2.LINE_AA)
                resized_frame = cv2.resize(frame['bgr'], (self.window_width, self.window_height))
                #cv2.imshow('frame', frame['bgr'])
                cv2.imshow('Ergo-Sight', resized_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            #Face Landmarks
            landmarks = []
            for face in frame['faces']:

                l, t, w, h = face
                rectangle = dlib.rectangle(left=int(l), top=int(t), right=int(l+w), bottom=int(t+h))
                landmarks_dlib = self.predictor(frame['gray'], rectangle)

                num_landmarks = landmarks_dlib.num_parts
                landmarks.append(np.array([tuple_from_dlib_shape(i, landmarks_dlib) for i in range(num_landmarks)]))


            # Extract the face region
            face_roi = gray[t:t + h, l:l + w]   
            frame['landmarks'] = landmarks

            #Eye Detector
            frame = crop_eye(frame)
            heatmaps = process_eyes (frame, self.gaze_model)
            
            # Eye Landmarks
            landmarks = find_landmarks(heatmaps)

            img, pitch = process_gaze (frame, landmarks, self.start_time)
            blink, predicted_emotion = self.emotion.predict_emotion(frame, face_roi, pitch)

            if predicted_emotion is None:
                continue

            # Increment the count for the predicted emotion
            self.emotion_counts[predicted_emotion] += 1

            ear = self.blink.blink_detector(landmarks_dlib)

            # Calculate the eye aspect ratio (EAR)
            if ear < self.blink.EYE_AR_THRESH:
                if blink:
                    self.total_blinks += 1
                    # print ("BLINK INSTANCE")
                # else:
                #      print ("NOT BLINK INSTANCE")


            # Check if the specified duration has elapsed
            elapsed_time = time.time() - self.start_time
            if elapsed_time >= self.emotion_duration:
                # Determine the dominant emotion
                self.dominant_emotion = self.emotion_counts.most_common(1)[0][0]
                print("Dominant emotion over {} seconds: {}".format(self.emotion_duration, self.dominant_emotion))

                self.file.save_progress("Detected-Emotion",self.dominant_emotion, self.file_path)

                if self.dominant_emotion == 'Fatigue':
                    if self.notify.eye_notification:
                        self.send_notification( "Feeling Tired?", "Take a Braek", "You Seems Tired!")
                    else:
                        beepy.beep(sound='error')

                # Reset emotion counts for the next duration
                self.emotion_counts.clear()
                self.start_time = time.time()

            #  Check if one minute has elapsed
            if blink: 
                elapsed_blink_time = time.time() - self.blink_start_time
                if elapsed_blink_time >= self.blink_duration:
                    if self.total_blinks < self.MIN_BLINK_THRESHOULD:
                        if self.notify.eye_notification:
                        # Send notification
                            self.send_notification("Blink Reminder", "Keep Blinking" ,"Don't forget to blink regularly for healthy eyes!")
                        else:
                            beepy.beep(sound='error')

                    elif self.total_blinks > self.MAX_BLINK_THRESHOULD :
                        if self.notify.eye_notification:
                        # Send notification
                            self.send_notification("Blink Alert!", "Take a Break!" ,"You've been blinking more frequently than usual.")
                        else:
                            beepy.beep(sound='error')

                    # Reset variables for the next minute
                    self.total_blinks = 0
                    self.blink_start_time = time.time()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        # When everything done, release the capture
        self.cap.release()
        cv2.destroyAllWindows()    

    def stop_monitoring (self):
        # Release the webcam capture and close OpenCV windows
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()