import time
import json

import pokr
import redis

from websocket import PokeSocket


r = redis.Redis()

class FilteredPrinter(object):
    def printer(self, data):
        if data['dithered_delta'] == '':
            return
        data.pop('frame')
        r.publish('pokemon', json.dumps(data))
        r.set('pokemon.dithered', data['dithered'])
        print data['timestamp']


proc = pokr.StreamProcessor(only_changes=False)
proc.add_handler(pokr.StringDeltaCompressor('dithered').handle)
proc.add_handler(FilteredPrinter().printer)
proc.run()


time.sleep(5)


print '\x1b[2J'
while True:
    time.sleep(1)
