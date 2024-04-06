import os 
from datetime import datetime
from Constants import DATE_FORMAT

class Job:
    def __init__(self, trends, imagePrompt, outputImagePath):
        self.trends = trends
        self.imagePrompt = imagePrompt
        self.outputImagePath = outputImagePath

    def trends_to_string(self):
        # Convert all trends to a formatted string
        return '\n'.join(str(trend) for trend in self.trends)

    def save_trends_to_file(self):
        trends_string = self.trends_to_string()

        # Ensure the 'jobs' directory exists
        os.makedirs('jobs', exist_ok=True)

        # Create a filename with today's date
        today = datetime.now().strftime(DATE_FORMAT)
        filename = f"jobs/trends_{today}.txt"

        # Save the string to a file
        with open(filename, 'w') as file:
            file.write(trends_string)