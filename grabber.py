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
        data.pop('screen')
        r.publish('pokemon.streams.frames', json.dumps(data))
        print data['timestamp'], '%5d'%len(data['dithered_delta'])

class DialogPusher(object):
    def handle(self, text, lines, timestamp):
        r.publish('pokemon.streams.dialog', json.dumps({'time': timestamp, 'text': text}))


box_reader = pokr.BoxReader()
box_reader.add_dialog_handler(DialogPusher().handle)

proc = pokr.StreamProcessor(frame_skip=0)
proc.add_handler(pokr.StringDeltaCompressor('dithered').handle)
proc.add_handler(box_reader.handle)
proc.add_handler(FilteredPrinter().printer)
proc.add_handler(pokr.LogHandler('text', 'frames.log').handle)
proc.run()

while True:
    time.sleep(1)
