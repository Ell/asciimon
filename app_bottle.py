from gevent import monkey; monkey.patch_all();

from bottle import request, Bottle, abort

import json
import redis
import gevent

app = Bottle()
red = redis.Redis()


@app.route('/')
def index():
    dithered = red.get('pokemon.dithered')
    return template('index.html', dithered=dithered)i


@app.route('/pokemon')
def pokestream(ws):
    ws = request.environ.get('wsgi.websocket')
    if not ws:
        abort(400, 'Expected WebSocket request.')

    pokesocket.register(ws)

    while True:
        gevent.sleep(120, ref=False)


class PokeSocket(object):
    def __init__(self, chan):
        self.red = redis.Redis()
        self.clients = []
        self.pubsub = self.red.pubsub()
        self.pubsub.subscribe(chan)
        self.dithered = ''

    def data_loop(self):
        for message in self.pubsub.listen():
            try:
                data = message['data']
                yield data
            except Exception:
                print "data_loop error"
                pass

    def register(self, client):
        self.clients.append(client)
        print 'client registered %d' % len(self.clients)
        gevent.spawn(self.send, client, '0\t' + self.dithered)

    def send(self, client, data):
        try:
            client.send(data)
        except Exception:
            self.clients.remove(client)

    def run(self):
        for data in self.data_loop():
            if isinstance(data, long):
                continue  # wtf

            items = json.loads(data)
            data = items['dithered_delta']
            self.dithered = items['dithered']

            if data != '':
                for client in self.clients:
                    # TODO: figure out how to mark a client as new and send a full update
                    self.send(client, data)
                    #gevent.spawn(self.send, client, data)

    def start(self):
        gevent.spawn(self.run)


if __name__ == '__main__':
    pokesocket = PokeSocket('pokemon')
    pokesocket.start()
    app.run(host='0.0.0.0', port=8000)
