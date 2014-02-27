#!/usr/bin/env python

import time
import json

import pokr
import redis


r = redis.Redis()

class FilteredPrinter(object):
    def printer(self, data):
        if data['dithered_delta'] == '':
            return
        data.pop('frame')
        r.publish('pokemon', json.dumps(data))
        r.set('pokemon.dithered', data['dithered'])
        print data['timestamp'], len(data['dithered_delta'])


proc = pokr.StreamProcessor(only_changes=False, frame_skip=0)
proc.add_handler(pokr.StringDeltaCompressor('dithered').handle)
proc.add_handler(FilteredPrinter().printer)
proc.add_handler(pokr.LogHandler('text', 'frames.log').handle)
proc.run()

while True:
    time.sleep(1)
