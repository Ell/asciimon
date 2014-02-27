from flask import Flask, render_template
from flask_sockets import Sockets

import redis
import gevent

from websocket import PokeSocket


SECRET_KEY = 'changme'

app = Flask(__name__)
app.config.from_object(__name__)
sockets = Sockets(app)

pokesocket = PokeSocket('pokemon')
pokesocket.start()

red = redis.Redis()


@app.route('/')
def index():
    dithered = red.get('pokemon.dithered')
    return render_template('index.html', dithered=dithered)


@sockets.route('/pokemon')
def pokestream(ws):
    pokesocket.register(ws)

    while True:
        gevent.sleep(120)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
