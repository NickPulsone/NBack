#!/usr/bin/env python
import datetime
from time import sleep
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import random
import csv
import pyttsx3
import time
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

if __name__ == "__main__":
    # Initialize engine for TTS
    engine = pyttsx3.init()
    engine.setProperty('rate', 100)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)

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

    # Define recording parameters and start recording
    rec_seconds = int(NUM_TESTS) * (INTERIAL_INTERVAL_S + STIMULUS_INTERVAL_S) + 10
    sample_rate = 44100
    myrecording = sd.rec(int(rec_seconds * sample_rate), samplerate=sample_rate, channels=1)
    recording_start_time = datetime.datetime.now()
    sleep(1)

    # Displays the text to the user for given number of iterations
    for i in range(NUM_TESTS):
        # Speak a letter (auditory stimulus), track global time of stimulus
        stim_start = time.time()
        engine.say(LETTERS[letter_index_sequence[i]])
        stimuli_time_stamps[i] = datetime.datetime.now()
        engine.runAndWait()
        engine.stop()
        # Wait out the stimuli delay
        while (time.time() - stim_start) < (STIMULUS_INTERVAL_S + INTERIAL_INTERVAL_S):
            sleep(0.001)


    # Stop the recording, save file as .wav
    print("Waiting for recording to stop...")
    sd.wait()
    wavfile.write(TRIAL_NAME + '.wav', sample_rate, myrecording)  # Save as WAV file
    print("Done. Saving data...")

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
    print("Done.")
    
