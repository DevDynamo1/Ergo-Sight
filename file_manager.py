import time
import os

class FileManager:
    # Delete old data
    def delete_old_data(self, file_path):
        if os.path.exists(file_path):
            current_date = time.strftime("%Y-%m-%d", time.localtime())
            with open(file_path, 'r') as file:
                lines = file.readlines()
            filtered_lines = [line for line in lines if line.startswith(current_date)]
            with open(file_path, 'w') as file:
                file.writelines(filtered_lines)  

    # Saving data
    def save_progress (self, title, result, file_path):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(file_path, 'a') as file:
            file.write("{} - {} : {}\n".format(timestamp, title, result))             