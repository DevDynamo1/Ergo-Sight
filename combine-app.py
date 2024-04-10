import rumps

from posture import PostureWatcher
from progress import Progress
from EmotionMonitor import EmotionMonitor
from notification import Notification
from file_manager import FileManager

import os

class Application(rumps.App):
    def __init__(self):
        super().__init__("ErgoSight", icon="IMAGES/logo.png")
        self.pw = None
        self.emotion_monitor = None
        # Track if the camera is started
        self.camera_started = False

        self.notify = Notification()
        self.file = FileManager ()

        self.file_path_posture = "FILES/posture_data.txt"
        self.file_path = "FILES/ergo-sight-progress.txt"
        self.conset_path = "FILES/consent.txt"

        self.posture_notify = True
        self.eye_notify = True

        self.progress = Progress()
        self.file.delete_old_data(self.file_path)
        self.file.delete_old_data(self.file_path_posture)

        # Create menu items
        self.posture_monitor = rumps.MenuItem('Posture Monitor')
        self.set_base_posture_menu = rumps.MenuItem('Set base posture', callback=self.set_base_posture)
        self.clear_base_posture_menu = rumps.MenuItem('Clear base posture', callback=self.clear_base_posture)
        self.progress_posture_menu = rumps.MenuItem('Progress', callback=self.progress_generator_posture)
        self.settings_menu = rumps.MenuItem('Settings')

        self.pos_text = rumps.MenuItem('Text Notification', callback=self.pos_notify_text)
        self.pos_sound = rumps.MenuItem('Sound Notification', callback=self.pos_notify_sound)

        self.settings_menu.add(self.pos_text)
        self.settings_menu.add(self.pos_sound)

        self.posture_monitor.add(self.set_base_posture_menu)
        self.posture_monitor.add(self.clear_base_posture_menu)
        self.posture_monitor.add(self.progress_posture_menu)
        self.posture_monitor.add(self.settings_menu)


        self.eye_strain = rumps.MenuItem('Eye-Strain Monitor')
        self.eye_strain_monitor = rumps.MenuItem('Monitor', callback=self.start_notifications)
        self.stop_monitor = rumps.MenuItem('Stop', callback=self.stop_monitoring)
        self.eye_strain_progress = rumps.MenuItem('Progress', callback=self.progress_generator)
        self.eye_settings_menu = rumps.MenuItem('Settings')

        self.eye_text = rumps.MenuItem('Text Notification', callback=self.eye_notify_text)
        self.eye_sound = rumps.MenuItem('Sound Notification', callback=self.eye_notify_sound)

        self.eye_settings_menu.add(self.eye_text)
        self.eye_settings_menu.add(self.eye_sound)       

        self.eye_strain.add(self.eye_strain_monitor)
        self.eye_strain.add(self.stop_monitor)
        self.eye_strain.add(self.eye_strain_progress)
        self.eye_strain.add(self.eye_settings_menu)

        # Add items to the main menu
        self.menu = [self.posture_monitor, self.eye_strain]
        
    # Getting user consent   
    def get_consent(self):
        if os.path.exists(self.conset_path):
            with open(self.conset_path, "r") as file:
                consent = file.read().strip()
                return consent == 'yes'
        else:
            return False
        
    # setting base posture    
    def set_base_posture(self, _):
        if self.get_consent():
            self.pw = PostureWatcher(notify=self.notify)  # Initialize PostureWatcher
            self.camera_started = True  # Update camera status
            self.pw.set_base_posture() 

        else : 
            # Getting user consent before accessing the webcam
            consent = rumps.alert(
                title="ErgoSight",
                message="Do you consent to access the webcam for posture monitoring?",
                ok="Yes",
                cancel="No"    
            )

            if consent:
                with open(self.conset_path, "w") as file:
                    file.write("yes")
                if not self.camera_started:  
                    self.pw = PostureWatcher(notify=self.notify)  
                    self.camera_started = True  
                self.pw.set_base_posture()      

    def clear_base_posture(self, _):
        self.pw.base_posture = None
        self.camera_started = False  # Update camera status
        self.pw = None
        self.title = "ErgoSight : ⚠️ Please set your base posture"

    @rumps.timer(5)
    def check_posture(self, _):
        if self.pw:
            self.pw.run()

    def progress_generator_posture(self, _):
        if self.progress:  # Check if the emotion monitor is initialized
            self.progress.show_pie_chart(self.file_path_posture, "Posture", "Posture-Progress")

    @rumps.timer(1)
    def update_title(self, _):
        if self.pw and not self.pw.base_posture:
            self.title = "⚠️ Please set your base posture."
        elif self.pw:
            cd = self.pw.deviation.current_deviation
            self.title = "ErgoSight : "
            if cd < 25:
                self.title += "✅ Great posture!"
            elif cd < 35:
                self.title += f"⚠️ Improve your posture! ({cd}%)"
            else:
                self.title += f"⛔️ Fix your posture! ({cd}%)"

    # Customize notifications            
    def pos_notify_sound(self, _):
        self.notify.posture_notification_setting (True)
                  
    def pos_notify_text(self, _):
        self.notify.posture_notification_setting (False)   

    def eye_notify_sound(self, _):
        self.notify.eye_notification_setting (False)
                  
    def eye_notify_text(self, _):
        self.notify.eye_notification_setting (True)           

    def start_notifications(self, _):

        if self.get_consent():
            self.emotion_monitor = EmotionMonitor(notify=self.notify)
            self.emotion_monitor.start_monitoring() 
        else : 
            consent = rumps.alert(
                title="ErgoSight",
                message="Do you consent to access the webcam for eye-strain monitoring?",
                ok="Yes",
                cancel="No"
            )

            if consent:  # If user consents
                with open(self.conset_path, "w") as file:
                    file.write("yes")
                self.emotion_monitor = EmotionMonitor(notify=self.notify)
                self.emotion_monitor.start_monitoring()

    def stop_monitoring(self, _):
        self.emotion_monitor.stop_monitoring()

    def progress_generator(self, _):
        if self.progress:  # Check if the emotion monitor is initialized
            self.progress.show_pie_chart(self.file_path, "Detected-Emotion", "Emotion-Progress")    

if __name__ == "__main__":
    app = Application()
    app.run()
