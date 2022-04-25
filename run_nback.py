#!/usr/bin/env python
import datetime
from time import sleep
import numpy as np
import sounddevice as sd
from scipy.io import wavfile, loadmat
import csv
import pyaudio
import time
""" ~~~~~~~~~~~~~     TUNABLE PARAMETERS     ~~~~~~~~~~~~~ """
# The N value in "N-Back" (usually 2)
N = 2

# Name of given trial
TRIAL_NAME = "2back_test_auditory"

# Colors dictionary that identifies the RGB values of the used colors
LETTERS = ["A", "B", "C", "D", "E", "H", "I", "K", "L", "M", "O", "P", "R", "S", "T"]

# Name of MATLAB file containing input sequence
MAT_FILE_NAME = "NBACK_2_VersionA.mat"

# Frequency of matching n back letters is 1:FREQUENCY (FREQUENCY = 4 means 1 in 4 responses should be "Yes")
FREQUENCY = 4

# Name of the matlab file containing stimulus info (include filepath if necessary)
NUM_TESTS = 20

# The minimum period, in milliseconds, that could distinguish two different responses
# STIMULUS_INTERVAL_S = 0.75
INTERIAL_INTERVAL_S = 2.5
"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

if __name__ == "__main__":
    # Load frequency data, convert to playable format
    Letters_Data = loadmat("Letters2.mat")
    New_Letters_Data = {}
    for letter in LETTERS:
        new_byte_data = bytes(Letters_Data[letter.lower()][0])
        New_Letters_Data[letter] = new_byte_data
    """
    # Initialize engine for TTS
    engine = pyttsx3.init()
    engine.setProperty('rate', 100)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    """

    # Get test sequence from mat file
    mat = loadmat(MAT_FILE_NAME)
    letter_sequence = mat["Sequence"]
    answer_array = mat["Answers"]

    # Creates an array that contains the global time for each time stamp
    stimuli_time_stamps = np.empty(NUM_TESTS, dtype=datetime.datetime)

    # Give the user a countdown
    print("Starting in...")
    for num in ["3..", "2..", "1.."]:
        print(num)
        sleep(1)
    print("GO!!!")
    sleep(1)

    # Define recording parameters and start recording
    rec_seconds = int(NUM_TESTS) * INTERIAL_INTERVAL_S + 10
    sample_rate = 44100
    myrecording = sd.rec(int(rec_seconds * sample_rate), samplerate=sample_rate, channels=1)
    recording_start_time = datetime.datetime.now()
    sleep(1)

    # Open a data stream to play audio
    p = pyaudio.PyAudio()
    stream = p.open(format=8, channels=1, rate=44100*4, output=True)

    print("Note: The first N stimuli warrant no response from subject.")
    # Says the letters to the user for given number of iterations
    for i in range(NUM_TESTS):
        # Display stimulus info
        print(f"Simulus {i+1}: Letter={letter_sequence[i]}, Answer={answer_array[i]}")
        # Speak a letter (auditory stimulus), track global time of stimulus
        stim_start = time.time()
        stimuli_time_stamps[i] = datetime.datetime.now()
        stream.write(New_Letters_Data[letter_sequence[i]])
        # Wait out the stimuli delay
        while (time.time() - stim_start) < INTERIAL_INTERVAL_S:
            sleep(0.001)

    # Terminate TTS stream
    stream.stop_stream()
    stream.close()
    p.terminate()

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
            writer.writerow([letter_sequence[i], answer_array[i], stimuli_time_stamps[i]])
    print("Done.")
