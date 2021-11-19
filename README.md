# NBack
Implements the psychological N-Back task. The N-Back task (usually either 1-back or 2-back) involves a sequence of visual stimuli in the form of letters. The user is instructed to say "Yes" if the letter presented on the screen was there N iterations ago, and "No" otherwise. The user should refrain from speaking for the first N stimuli.

Requires Python 3.9. Edit tunable paramaters as necessary in both "run_nback.py" and "process_nback.py", ensuring the parameters match up.

IMPORTANT: Include the files in this drive link in your working directory (too big for github): https://drive.google.com/drive/folders/1_XCEDEXR9AgY9L-dRdYDVTmz9gXPXfcK?usp=sharing

"run_nback.py" will run the test on a subject and save an audio file and csv file with the relevant data. "process_nback.py" will use this data to calculate reaction times, accuracies, etc. Post processing is mostly automatic, but does require review from a user to doule check the responses.
