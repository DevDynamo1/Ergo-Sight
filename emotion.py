import cv2
from collections import Counter
import numpy as np
from keras.models import load_model

class EmotionDetector:

    def __init__(self):

        # Define class names
        self.class_names = ["None", "Fatigue", "Glare", "Normal", "Squint"]

        # Define the time window size in frames
        self.window_size = 30
        # Threshold for majority decision  
        self.threshold = self.window_size // 2  
        # Smoothing window size for moving average
        self.smoothing_window = 3  

        self.state_window = []
        self.smoothed_predictions = []
        
        # Models paths
        self.emotion_model = load_model('MODEL/model.h5')  
        # self.emotion_model = load_model("MODEL/best_model.h5")

    def predict_emotion(self, frame, face_roi, pitch):
        try:
            # Preprocess the face image for model prediction
            face_resized = cv2.resize(face_roi, (48, 48))
            face_normalized = face_resized / 255.0
            face_input = np.expand_dims(face_normalized, axis=-1)  # Add channel dimension

            # Predict emotion using the model
            emotion_probabilities = self.emotion_model.predict(np.expand_dims(face_input, axis=0))
            predicted_class_index = np.argmax(emotion_probabilities)
            predicted_class = self.class_names[predicted_class_index]

            # Update state window
            self.state_window.append(predicted_class)
            if len(self.state_window) > self.window_size:
                self.state_window.pop(0)

            # Count occurrences of states in the window
            state_counts = Counter(self.state_window)

            # Decide the overall state based on majority vote
            if state_counts["Fatigue"] + state_counts["Squint"] + state_counts["Glare"] + state_counts["None"] > self.threshold:
                overall_state = "Fatigue"
                blink = False
            else:
                overall_state = "Normal"
                blink = True


            # Add the prediction to smoothed predictions
            self.smoothed_predictions.append(overall_state)

            # Apply moving average smoothing
            if len(self.smoothed_predictions) > self.smoothing_window:
                self.smoothed_predictions.pop(0)
                overall_state = Counter(self.smoothed_predictions).most_common(1)[0][0]    

            # Filter out instances where the user is looking downwards (towards the keyboard)
            if pitch < -np.pi/9:  # Adjust this threshold as needed
                overall_state = "Normal"     
        
            # Add emotion prediction text overlay to the frame
            emotion_text = "Predicted Emotion: " + overall_state
            cv2.putText(frame['bgr'], overall_state, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            resized_frame = cv2.resize(frame['bgr'], (300, 200))
            cv2.imshow('Ergo-Sight', resized_frame)

        # test add
            return blink, overall_state
        
        except Exception as e:
            print("Error ",e)

            return blink, None
