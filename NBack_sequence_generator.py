#!/usr/bin/env python
import numpy as np
from scipy.io import savemat
import random

""" ~~~~~~~~~~~~~     TUNABLE PARAMETERS     ~~~~~~~~~~~~~ """
# Colors dictionary that identifies the RGB values of the used colors
LETTERS = ["A", "B", "C", "D", "E", "H", "I", "K", "L", "M", "O", "P", "R", "S", "T"]
# Number of total tests (pairs of letters that warrant a response, not individual letters)
NUM_TESTS = 75
# Value for N
N = 1
# Frequency (1/Frequency = roughly proportion of yesses that warrant a "Yes" response
FREQUENCY = 3
"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

if __name__ == "__main__":
    # Create test sequence and corresponding array containing correct answers (Y/N)
    random.seed()
    letter_index_sequence = np.empty(NUM_TESTS, dtype=int)
    correct_answers = np.empty(NUM_TESTS, dtype=str)
    for i in range(0, N):
        correct_answers[i] = "N"
    for i in range(NUM_TESTS):
        # Generate a yes case
        if (i > N) and (random.randint(0, FREQUENCY - 1) == 0):
            letter_index_sequence[i] = letter_index_sequence[i-N]
            correct_answers[i] = "Y"
        # Generate a no case
        else:
            random_index = random.randint(0, len(LETTERS)-1)
            if i >= N:
                while random_index == letter_index_sequence[i-N]:
                    random_index = random.randint(0, len(LETTERS) - 1)
            letter_index_sequence[i] = random_index
            correct_answers[i] = "N"
    # Generate the sequence of letters from randomly generated indices
    letter_sequence = np.empty(len(letter_index_sequence), dtype=str)
    for i in range(len(letter_index_sequence)):
        letter_sequence[i] = LETTERS[letter_index_sequence[i]]
    print(letter_sequence)
    print(correct_answers)
    # Create dictionary containing the generated data
    mdic = {"Sequence": letter_sequence, "Answers": correct_answers}
    # Save dictionary as a mat file to be used
    savemat("NBACK_1_VersionC.mat", mdic)
