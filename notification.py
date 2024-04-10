import rumps

class Notification:
    def __init__(self):
        self.posture_notification = True        
        self.eye_notification = True

    def send_notification(self, title, subtitle, message):
        rumps.notification(title = title, subtitle = subtitle, message = message, sound=True)    

    def posture_notification_setting (self, type):
        self.posture_notification = type

    def eye_notification_setting (self, type):
        self.eye_notification = type            
