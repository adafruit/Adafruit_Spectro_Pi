"""
NextBus prediction class.  For each route/stop, NextBus server is polled
automatically at regular intervals.  Front-end app just needs to init
this with stop data, which can be found using the routefinder.py script.
"""

# pylint: disable=bad-option-value, useless-object-inheritance

import threading
import time
try:
    from urllib import request  # Python 3
except ImportError:
    import urllib as request    # Python 2
from xml.dom.minidom import parseString

class Predict(object):
    """NextBus prediction class.  For each route/stop, NextBus server
       is polled automatically at regular intervals.  Front-end app
       just needs to init this with stop data, which can be found
       using the routefinder.py script."""
    interval = 120     # Default polling interval = 2 minutes
    initial_sleep = 0  # Stagger polling threads to avoid load spikes

    # Predict object initializer.  1 parameter, a 4-element tuple:
    # First element is agengy tag (e.g. 'actransit')
    # Second is line tag (e.g. '210')
    # Third is stop tag (e.g. '0702630')
    # Fourth is direction -- not a tag, this element is human-readable
    # and editable (e.g. 'Union Landing') -- for UI purposes you may
    # want to keep this short.  The other elements MUST be kept
    # verbatim as displayed by the routefinder.py script.
    # Each Predict object spawns its own thread and will perform
    # periodic server queries in the background, which can then be
    # read via the predictions[] list (est. arrivals, in seconds).
    def __init__(self, data):
        self.data = data
        self.predictions = []
        self.last_query_time = time.time()
        thread = threading.Thread(target=self.thread)
        thread.daemon = True
        thread.start()

    def thread(self):
        """Periodically get predictions from server."""
        initial_sleep = Predict.initial_sleep
        Predict.initial_sleep += 5  # Thread staggering may
        time.sleep(initial_sleep)   # drift over time, no problem
        while True:
            dom = Predict.req('predictions' +
                              '&a=' + self.data[0] + # Agency
                              '&r=' + self.data[1] + # Route
                              '&s=' + self.data[2])  # Stop
            if dom is None:
                return  # Connection error
            self.last_query_time = time.time()
            predictions = dom.getElementsByTagName('prediction')
            new_list = []
            for prediction in predictions:  # Build new prediction list
                new_list.append(
                    int(prediction.getAttribute('seconds')))
            new_list.sort()
            self.predictions = new_list # Replace current list
            time.sleep(Predict.interval)

    @staticmethod
    def req(cmd):
        """Open URL, send request, read & parse XML response."""
        xml = None
        try:
            connection = request.urlopen(
                'http://webservices.nextbus.com'  +
                '/service/publicXMLFeed?command=' + cmd)
            raw = connection.read()
            connection.close()
            xml = parseString(raw)
        finally:
            pass
        return xml

    @staticmethod
    def set_interval(i):
        """Set polling interval (in seconds) for ALL Predict objects."""
        Predict.interval = i
