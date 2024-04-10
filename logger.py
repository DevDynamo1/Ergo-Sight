from os import system, name
from threading import Lock
from termcolor import colored
import time
import beepy
from notification import Notification


def clear_console():
    if name == 'nt':  # windows
        system('cls')

    else:  # linux
        system('clear')


class Logger:
    """
    A simpler logger class.
    """

    def __init__(self, logger_name: str):
        self.name = logger_name
        self.lock = Lock()

    # def send_notification(self, title, subtitle, message):
    #     rumps.notification(title = title, subtitle = subtitle, message = message, sound=True)    

    def notify(self, message: str, color: str = 'white', with_sound: bool = False, type: bool = True):

        self.lock.acquire()
        print(colored(f'[{time.strftime("%H:%M:%S", time.localtime())}] {message}', color))
        self.lock.release()

        if with_sound:
            if type: 
                beepy.beep(sound='error')
            else:
                Notification.send_notification("Posture Alert!","FIX your posture","Remember to sit up straight to maintain a healthy posture")

                