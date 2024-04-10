import plotly.express as px
import datetime


class Progress :

    def show_pie_chart(self, file_path, context, title):
        # Read data from the saved file
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Extract the detected emotions from the file
        detected_emotions = []
        for line in lines:
            if context in line:
                emotion = line.split(" : ")[-1].strip()
                detected_emotions.append(emotion)

        # Count occurrences of each emotion
        emotions_count = {}
        for emotion in detected_emotions:
            if emotion in emotions_count:
                emotions_count[emotion] += 1
            else:
                emotions_count[emotion] = 1

        # Create a pie chart using Plotly Express
        labels = list(emotions_count.keys())
        counts = list(emotions_count.values())

        # Adding current date to the title
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        title_with_date = f"{title} - {current_date}"

        fig = px.pie(names=labels, values=counts, title=title_with_date)

        # Show the pie chart
        fig.show() 