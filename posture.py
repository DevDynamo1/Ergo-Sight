import cv2
import logger as logger

from detector import PoseDetector, PoseLandmarks
from deviation import Deviation
from logger import Logger
from typing import Union
import time
from notification import Notification
from file_manager import FileManager

class BasePosture:
    """
    Wrapper for Mediapipe Pose Landmarks
    """

    def __init__(self, nose: float, left_shoulder: float, right_shoulder: float):
        self.nose = nose
        self.left_shoulder = left_shoulder
        self.right_shoulder = right_shoulder
        


class PostureWatcher:
    """
    PostureWatcher is responsible for monitoring the posture of a user.
    It uses PoseDetector to compare the user's current posture to the base posture.
    """

    def __init__(self,
                 deviation_algorithm=2,
                 deviation_interval=5,
                 deviation_adjustment=5,
                 deviation_threshold=25,
                 deviation_buffer=3,
                 base_posture=None,
                 debug=True,
                 notify=Notification(),):
        
        
        """
        Initializes the PostureWatcher.
        :param deviation_algorithm: The algorithm used to calculate the deviation.
        :param deviation_interval: The interval in seconds between checking for deviation
        :param deviation_adjustment: The amount of deviation to allow before triggering an alert
        :param deviation_threshold: The threshold at which a deviation should trigger an alert
        :param deviation_buffer: The number of consecutive deviations to allow before triggering an alert
        :param base_posture: The base posture to compare to
        :param debug: Whether to print debug messages
        """
        self.detector = PoseDetector()
        self.deviation = Deviation(threshold=deviation_threshold, max_buffer=deviation_buffer)

        self.cap = None


        self.base_posture = base_posture
        self.deviation_algorithm = deviation_algorithm
        self.deviation_interval = deviation_interval
        self.deviation_adjustment = deviation_adjustment

        self.thread = None
        self.debug = debug
        self.logger = Logger('PW')
        self.file_path = "FILES/posture_data.txt"
        self.notify = notify
        self.file = FileManager()

    def get_video_capture_device(self):
        # Check if cv2.VideoCapture(1) is available
        if cv2.VideoCapture(1).isOpened():
            return cv2.VideoCapture(1)
        else:
            return cv2.VideoCapture(0)       

    def run(self):
        """
        Finds a pose, compares it to the base posture, and notifies the user if the deviation is above the threshold.
        """
        if not self.base_posture:
            return

        _, img = self.cap.read()
        img, _ = self.detector.find_pose(img)
        self.deviation.current_deviation = self._get_deviation_from_base_posture()
        self._handle_deviation()

    def stop(self):
        """
        Stops Posture Watcher and destroys allocated resources.
        """
        self.cap.release()
        cv2.destroyAllWindows()

    def set_base_posture(self):
        self.cap = self.get_video_capture_device()
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.last_fps_calc_timestamp = 0
        _, img = self.cap.read()
        _, lm = self.detector.find_pose(img)

        if lm:
            nose = lm[PoseLandmarks.NOSE]
            l_shoulder = lm[11]
            r_shoulder = lm[12]
            self.base_posture = BasePosture(nose, l_shoulder, r_shoulder)

    def _get_deviation_from_base_posture(self) -> Union[int or None]: # type: ignore

        if self.base_posture is None:
            return None

        _, img = self.cap.read()
        _, lm = self.detector.find_pose(img)
        deviation = 100

        if not lm:  # No pose found
            return deviation
        
        nose = abs(self.base_posture.nose.x - lm[0].x) + abs(self.base_posture.nose.y - lm[0].y) + abs(
            self.base_posture.nose.z - lm[0].z)

        l_shoulder = abs(self.base_posture.left_shoulder.x - lm[11].x) + abs(self.base_posture.left_shoulder.y - lm[11].y) + \
            abs(self.base_posture.left_shoulder.z - lm[11].z)
        r_shoulder = abs(self.base_posture.right_shoulder.x - lm[12].x) + abs(self.base_posture.right_shoulder.y - lm[12].y) + \
            abs(self.base_posture.right_shoulder.z - lm[12].z)

        deviation = int(

            ((nose + l_shoulder + r_shoulder) / (self.base_posture.nose.x + self.base_posture.left_shoulder.x +
                self.base_posture.right_shoulder.x) * 100))

        adjusted_deviation = 100 if deviation >= 100 else int(deviation - self.deviation_adjustment)
        return adjusted_deviation

    def _log_deviation(self, cd: int, buffer: int):
        """
        Logs the deviation using the built-in logging utility.
        :return: None
        """
        logger.clear_console()

        if self.deviation.has_deviated():
            self.logger.notify(f"Detected deviation from base posture by {cd}%", color='red', with_sound=True, type=self.notify.posture_notification)
        else:
            if cd < 25:
                self.logger.notify(f"✅ Great posture! {cd}% (Buf: {buffer})", color='green')
                self.file.save_progress ("Posture","Good-Posture", self.file_path)
            elif cd < 35:
                self.logger.notify(f"⚠️ Improve your posture! {cd}% (Buf: {buffer})", color='yellow')
                self.file.save_progress ("Posture","Neutral-Posture", self.file_path)
            else:
                self.logger.notify(f"️ Fix your posture! {cd}% (Buf: {buffer})", color='red')
                self.file.save_progress ("Posture","Poor-Posture", self.file_path)

        if self.debug:
            self.logger.notify(f"Deviation buffer: {buffer}", color='white')

    def _handle_deviation(self):
        """
        Handles the deviation from the base posture and notifies the user if the deviation is above the threshold.
        """
        if self.deviation.current_deviation is None:
            return

        cd = self.deviation.current_deviation
        buffer = self.deviation.current_buffer

        self._log_deviation(cd, buffer)

