#!/usr/bin/env python
import numpy as np
from pydub import silence, AudioSegment
import csv
import soundfile
import speech_recognition as sr
import os

""" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  TUNABLE PARAMETERS    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ """
# Trial name (subject name, etc)
TRIAL_NAME = "test1"
CSV_FILENAME = "test1.csv"

# The N value in "N-Back" (usually 2)
N = 2

# Colors dictionary that identifies the RGB values of the used colors
LETTERS = ["A", "B", "C", "D", "E", "H", "I", "K", "L", "M", "O", "P", "R", "S", "T"]

# Name of the matlab file containing stimulus info (include filepath if necessary)
NUM_TESTS = 25

# The highest audio level (in dB) the program will determine to be considered "silence"
SILENCE_THRESHOLD_DB = -20.0
MIN_PERIOD_SILENCE_MS = 1000

# The minimum period, in milliseconds, that could distinguish two different responses
STIMULUS_INTERVAL_S = 0.75
INTERIAL_INTERVAL_S = 2.00
""" ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ """


# Normalize audio file to given target dB level - https://stackoverflow.com/questions/59102171/getting-timestamps-from-audio-using-pythons
def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


if __name__ == "__main__":
    # Open CSV file, read in letters array and stimuli time stamps
    file = open(CSV_FILENAME)
    reader = csv.reader(file)
    header = next(reader)
    data = []
    for row in reader:
        if len(row) > 0:
            data.append(row)
    data = np.array(data)
    letter_sequence = np.array(data[:, 0], dtype=str)
    letter_index_sequence = np.array(data[:, 1], dtype=int)
    correct_answers = np.array(data[:, 2], dtype=str)
    stimuli_time_stamps = np.array(data[:, 3], dtype=float)

    # Open .wav with pydub
    audio_segment = AudioSegment.from_wav(TRIAL_NAME + ".wav")
    rec_seconds = audio_segment.duration_seconds

    # Normalize audio_segment to a threshold
    normalized_sound = match_target_amplitude(audio_segment, SILENCE_THRESHOLD_DB)

    # Generate nonsilent chunks (start, end) with pydub
    response_timing_chunks = np.array(
        silence.detect_nonsilent(normalized_sound, min_silence_len=MIN_PERIOD_SILENCE_MS, silence_thresh=SILENCE_THRESHOLD_DB,
                         seek_step=1))

    # If unable to detect nonsilence, end program and notify user
    if len(response_timing_chunks) == 0:
        print("Could not detect user's responses. Silence threshold/Minimum silence period may need tuning.")
        exit(1)

    # Calculate the time that the user starts to speak in each nonsilent "chunk"
    response_timing_markers = np.array(response_timing_chunks[:, 0]) / 1000.0
    while response_timing_markers[0] == 0.0:
        response_timing_markers = np.delete(response_timing_markers, 0)
        response_timing_chunks = np.delete(response_timing_chunks, 0, 0)

    # Create a folder to store the individual responses as clips to help determine
    # response accuracies later on.
    clip_seperation_path = TRIAL_NAME + "_reponse_chunks"
    if not os.path.isdir(clip_seperation_path):
        os.mkdir(clip_seperation_path)
    # How much we add (ms) to the ends of a clip when saved
    clip_threshold = 600
    for i in range(len(response_timing_chunks)):
        chunk = response_timing_chunks[i]
        chunk_filename = os.path.join(clip_seperation_path, f"chunk{i}.wav")
        # Save the chunk as a serperate wav, acounting for the fact it could be at the very beggining or end
        if chunk[0] <= clip_threshold:
            (audio_segment[0:chunk[1] + clip_threshold]).export(chunk_filename, format="wav")
        elif chunk[1] >= ((rec_seconds * 1000.0) - clip_threshold - 1):
            (audio_segment[chunk[0] - clip_threshold:(rec_seconds * 1000) - 1]).export(chunk_filename, format="wav")
        else:
            (audio_segment[chunk[0] - clip_threshold:chunk[1] + clip_threshold]).export(chunk_filename,
                                                                                        format="wav")
        # Reformat the wav files using soundfile to allow for speech recongition, and store in folder
        data, samplerate = soundfile.read(chunk_filename)
        soundfile.write(chunk_filename, data, samplerate, subtype='PCM_16')

    # Create an array to hold users response accuracy (TRUE, FALSE, or N/A)
    response_accuracies = []

    # Init the speech to text recognizer
    r = sr.Recognizer()

    # Create an array to hold raw user responses
    raw_responses = []

    # Calculate the reponse times given the arrays for response_timing_markers and stimuli_time_stamps
    reaction_times = []
    clip_index_array = np.empty(NUM_TESTS, dtype=int)
    for i in range(NUM_TESTS):
        rt = float('nan')
        clip_index_array[i] = -1
        # If there is no response after a time stamp, clearly the user failed to respond...
        if (i >= N) and (letter_index_sequence[i] == letter_index_sequence[i-N]):
            # Determine the most accurate nonsilent chunk that is associated with a given iteration
            for j in range(len(response_timing_markers)):
                if response_timing_markers[j] > stimuli_time_stamps[i]:
                    # If reaction is too fast, it means the program is considering a delayed response from previous stimulus
                    # Thus, we should continue the loop if that is the case, otherwise, break and store the reaction time
                    if response_timing_markers[j] - stimuli_time_stamps[i] < 0.1 \
                            and reaction_times[-1] > (STIMULUS_INTERVAL_S + INTERIAL_INTERVAL_S):
                        continue
                    rt = response_timing_markers[j] - stimuli_time_stamps[i]
                    break
            # If there is no nonsilent chunk after the time that the stimulus is displayed, store reaction time as "nan"
            # Also if the user's response is over the delay time and after the stimulus is displayed, then we know they either failed to
            # respond or the audio was not recorded and intepreted properly.
            if j >= len(response_timing_markers) or rt > (STIMULUS_INTERVAL_S + INTERIAL_INTERVAL_S):
                reaction_times.append(float('nan'))
                raw_responses.append("N/A")
                response_accuracies.append("FALSE")
                continue
            else:
                # Save index to clip index array
                clip_index_array[i] = j
                # If the response was valid, detemine if it was correct using speech recognition
                with sr.AudioFile(os.path.join(clip_seperation_path, f"chunk{j}.wav")) as source:
                    # listen for the data (load audio to memory)
                    audio_data = r.record(source)
                    # recognize (convert from speech to text)
                    resp = "Undetected"
                    try:
                        resp = (r.recognize_google(audio_data).split()[0])
                        if isinstance(resp, str):
                            resp = resp.upper()
                    except sr.UnknownValueError as err:
                        response_accuracies.append("N/A")
                        raw_responses.append("N/A")
                        reaction_times.append(rt)
                        continue
                    if resp[0] == correct_answers[i]:
                        response_accuracies.append("TRUE")
                        raw_responses.append(resp)
                    # If word not found, store response and mark as false
                    else:
                        response_accuracies.append("FALSE")
                        raw_responses.append(resp)
        else:
            # Check if user responded. If so, they are incorrect, if not they are correct.
            for j in range(len(response_timing_markers)):
                if response_timing_markers[j] > stimuli_time_stamps[i] and response_timing_markers[j] - stimuli_time_stamps[i] <= (STIMULUS_INTERVAL_S + INTERIAL_INTERVAL_S):
                    with sr.AudioFile(os.path.join(clip_seperation_path, f"chunk{j}.wav")) as source:
                        # listen for the data (load audio to memory)
                        audio_data = r.record(source)
                        # recognize (convert from speech to text)
                        resp = "Undetected"
                        try:
                            resp = (r.recognize_google(audio_data).split()[0])
                            if isinstance(resp, str):
                                resp = resp.upper()
                            response_accuracies.append("FALSE")
                            reaction_times.append(response_timing_markers[j] - stimuli_time_stamps[i])
                            raw_responses.append(resp)
                            clip_index_array[i] = j
                            break
                        except sr.UnknownValueError as err:
                            continue
            # Test if the loop was broken out of. If so move on, if not, we know the user was right
            if j >= len(response_timing_markers) - 1:
                response_accuracies.append("TRUE")
                raw_responses.append("N/A")
            else:
                continue
        reaction_times.append(rt)

    # Create another array to label each reactiontime according to if it was within the alloted time or not
    reaction_on_time = np.empty(NUM_TESTS, dtype=bool)
    for i in range(NUM_TESTS):
        if len(raw_responses[i]) > 0 and raw_responses[i] != "N/A" and reaction_times[i] > (STIMULUS_INTERVAL_S + INTERIAL_INTERVAL_S):
            reaction_on_time[i] = False
        else:
            reaction_on_time[i] = True

    # Write results to file
    with open(TRIAL_NAME + "_RESULTS.csv", 'w') as reac_file:
        writer = csv.writer(reac_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(
            ['LETTER', 'Correct Answer', 'User response', 'Accuracy (T/F)', 'Reaction time (s)',
             'Reaction on time (T/F)', 'Clip Index'])
        for i in range(NUM_TESTS):
            writer.writerow([letter_sequence[i], correct_answers[i], raw_responses[i], response_accuracies[i],
                             reaction_times[i], reaction_on_time[i], clip_index_array[i]])
    print("Done")
