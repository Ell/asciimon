import json
import redis
import gevent


class PokeSocket(object):
    def __init__(self, chan):
        self.red = redis.Redis()
        self.clients = []
        self.pubsub = self.red.pubsub()
        self.pubsub.subscribe(chan)

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

            if data != '':
                for client in self.clients:
                    # TODO: figure out how to mark a client as new and send a full update
                    gevent.spawn(self.send, client, data)

    def start(self):
        gevent.spawn(self.run)
