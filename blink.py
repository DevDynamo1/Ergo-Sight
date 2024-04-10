from scipy.spatial import distance as dist
from imutils import face_utils

class BlinkDetector:
    def __init__(self):

        # Define constants for blink detection
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES_MIN = 2
        self.EYE_AR_CONSEC_FRAMES_MAX = 4

    # Function to calculate eye aspect ratio (EAR)
    def eye_aspect_ratio(self, eye):
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear
    
    # Blink detector function
    def blink_detector (self, landmarks_dlib,):
        shapes = face_utils.shape_to_np(landmarks_dlib)

        left_eye = shapes[36:42]
        right_eye = shapes[42:48]

        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)

        ear = (left_ear + right_ear) / 2.0

        return ear