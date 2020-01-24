#!/usr/bin/env python

"""
Super simple NextBus display thing (prints to console).
"""

# pylint: disable=superfluous-parens

import time
from nextbus_predict import Predict

# List of bus lines/stops to predict.  Use nextbus_routefinder.py to look
# up lines/stops for your location, copy & paste results here.  The 4th
# element on each line can then be edited for brevity if desired.
STOPS = [
    ('lametro', '79', '11086', 'Downtown LA'),
    ('lametro', '79', '2549', 'Arcadia Station'),
    ('lametro', '260', '11086', 'Altadena'),
    ('lametro', '260', '2549', 'Artesia Station')
]

# Populate a list of predict objects from STOPS[].  Each then handles
# its own periodic NextBus server queries.  Can then read or extrapolate
# arrival times from each object's predictions[] list (see code later).
PREDICT_LISTE = []
for stop in STOPS:
    PREDICT_LISTE.append(Predict(stop))

time.sleep(1) # Allow a moment for initial results

while True:
    CURRENT_TIME = time.time()
    print('')
    for pl in PREDICT_LISTE:
        print(pl.data[1] + ' ' + pl.data[3] + ':')
        if pl.predictions: # List of arrival times, in seconds
            for p in pl.predictions:
                # Extrapolate from predicted arrival time,
                # current time and time of last query,
                # display in whole minutes.
                t = p - (CURRENT_TIME - pl.last_query_time)
                print('\t' + str(int(t/60)) + ' minutes')
        else:
            print('\tNo predictions')
    time.sleep(5) # Refresh every ~5 seconds
