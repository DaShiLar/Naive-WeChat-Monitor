# coding=utf-8
# Python Version: 3.5.1

# Flask
from flask import Flask, request, g

# gevent
from gevent import monkey
from gevent.pywsgi import WSGIServer
# monkey.patch_all()
# gevent end

import time

app = Flask(__name__)
app.config.update(DEBUG=True)


@app.route('/asyn/', methods=['GET'])
def test_asyn_one():
    print("asyn has a request!")
    time.sleep(10)
    return 'hello asyn'


@app.route('/test/', methods=['GET'])
def test():
    return 'hello test'


if __name__ == "__main__":
    app.run()
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()