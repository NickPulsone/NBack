#!/usr/bin/env python
import ctypes
import datetime
from time import sleep
import cv2
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import random
import csv

""" ~~~~~~~~~~~~~     TUNABLE PARAMETERS     ~~~~~~~~~~~~~ """
# The N value in "N-Back" (usually 2)
N = 2

# Name of given trial
TRIAL_NAME = "test1"

# Colors dictionary that identifies the RGB values of the used colors
LETTERS = ["A", "B", "C", "D", "E", "H", "I", "K", "L", "M", "O", "P", "R", "S", "T"]

# Frequency of matching n back letters is 1:FREQUENCY (FREQUENCY = 4 means 1 in 4 responses should be "Yes")
FREQUENCY = 4

# Name of the matlab file containing stimulus info (include filepath if necessary)
NUM_TESTS = 25

# The minimum period, in milliseconds, that could distinguish two different responses
STIMULUS_INTERVAL_S = 0.75
INTERIAL_INTERVAL_S = 2.00
"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

# Get screen dimensions
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# Make sure cv2 images are displayed in full screen
window_name = 'projector'
cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.moveWindow(window_name, screensize[1] - 1, screensize[0] - 1)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Create a blank white image as a template
img = np.full((screensize[1], screensize[0], 3), fill_value=255, dtype=np.uint8)

# Define text parameters for stimuli images
font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 15.0
fontThickness = 40
countDownFontScale = 7.0
coutDownFontThickness = 28


if __name__ == "__main__":
    # Create test sequence and corresponding array containing correct answers (Y/N)
    random.seed()
    letter_index_sequence = np.empty(NUM_TESTS, dtype=int)
    correct_answers = np.empty(NUM_TESTS, dtype=str)
    for i in range(0, N):
        correct_answers[i] = "N"
    for i in range(NUM_TESTS):
        if (i > N) and (random.randint(0, FREQUENCY - 1) == 0):
            letter_index_sequence[i] = letter_index_sequence[i-N]
            correct_answers[i] = "Y"
        else:
            random_index = random.randint(0, len(LETTERS)-1)
            if i >= N:
                while random_index == letter_index_sequence[i-N]:
                    random_index = random.randint(0, len(LETTERS) - 1)
            letter_index_sequence[i] = random_index
            correct_answers[i] = "N"

    # Creates an array that contains the global time for each time stamp
    stimuli_time_stamps = np.empty(NUM_TESTS, dtype=datetime.datetime)

    # Create an array of stimuli images
    stimuli_images = []
    for i in range(len(LETTERS)):
        # Copy the template image
        new_img = np.copy(img)

        # Determine text size from given word
        textsize = cv2.getTextSize(LETTERS[i], font, 1, 2)[0]

        # Define parameters for positioning text on a given blank image
        textX = int((img.shape[1] - textsize[0] * fontScale) / 2)
        textY = int((img.shape[0] + textsize[1] * fontScale) / 2)
        bottomLeftCornerOfText = (textX, textY)

        # Position text on the screen
        cv2.putText(new_img, LETTERS[i],
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    color=(0, 0, 0),
                    thickness=fontThickness)

        # Add the image to the array
        stimuli_images.append(new_img)

    # Give user a countdown
    for word in ["Get Ready...", "3..", "2..", "1..", "GO!!!"]:
        # Copy blank image from template
        new_img = np.copy(img)

        # Determine text size
        textsize = cv2.getTextSize(word, font, 1, 2)[0]

        # Define parameters for positioning text on template image
        textX = int((img.shape[1] - textsize[0] * countDownFontScale) / 2)
        textY = int((img.shape[0] + textsize[1] * countDownFontScale) / 2)
        bottomLeftCornerOfText = (textX, textY)

        # Position text on the screen
        cv2.putText(new_img, word,
                    bottomLeftCornerOfText,
                    font,
                    countDownFontScale,
                    color=(0, 0, 0),  # make the words black
                    thickness=coutDownFontThickness)

        # Wait out a 1s delay, then destory the image
        cv2.imshow(window_name, new_img)
        cv2.waitKey(1)
        sleep(1.0)
    sleep(0.5)

    # Define recording parameters and start recording
    rec_seconds = int(NUM_TESTS) * (INTERIAL_INTERVAL_S + STIMULUS_INTERVAL_S) + 10
    sample_rate = 44100
    myrecording = sd.rec(int(rec_seconds * sample_rate), samplerate=sample_rate, channels=1)
    recording_start_time = datetime.datetime.now()
    sleep(1)

    # Displays the text to the user for given number of iterations
    for i in range(NUM_TESTS):
        # Show image add the given array position to the user
        cv2.imshow(window_name, stimuli_images[letter_index_sequence[i]])
        # Get global time of stimulus
        stimuli_time_stamps[i] = datetime.datetime.now()
        # Wait out the given delay, then destory the image
        cv2.waitKey(1)
        sleep(STIMULUS_INTERVAL_S)
        # Show blank image in between stimuli
        cv2.imshow(window_name, img)
        # Wait out the given delay, then destory the image
        cv2.waitKey(1)
        sleep(INTERIAL_INTERVAL_S)

    # Destroy last displayed image
    cv2.destroyAllWindows()

    # Stop the recording, save file as .wav
    print("Waiting for recording to stop...")
    sd.wait()
    wavfile.write(TRIAL_NAME + '.wav', sample_rate, myrecording)  # Save as WAV file
    print("Done.")

    # Calculate the time at which each stimulus is displayed with respect to the start of the recording
    stimuli_time_stamps = np.array(
        [(stimuli_time_stamps[i] - recording_start_time).total_seconds() for i in range(NUM_TESTS)])

    # Write results to file
    with open(TRIAL_NAME + ".csv", 'w') as reac_file:
        writer = csv.writer(reac_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Letter', 'Letter index', 'Correct answer', 'Stimuli time from start (s)'])
        for i in range(NUM_TESTS):
            writer.writerow([LETTERS[letter_index_sequence[i]], letter_index_sequence[i], correct_answers[i],
                             stimuli_time_stamps[i]])
    print("Done")
