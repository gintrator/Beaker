from server import Server
from beaker import Beaker

port = 5000
app = Beaker("Beaker Application v0.1.")

@app.produces('text/html')
@app.get('/')
def index(req, res):
    html = ["<h1>Welcome to a Beaker app!</h1>",
            "<p>This is a sample beaker application.</p>",
            "<p>It's used to build simple RESTful services.</p>",
            "<p>It's very much like Flask, except that I wrote it.</p>",
            "<p>Check out a <a href='/json'>json endpoint</a></p>",
            "</br>",
            "<p>by Gabriel Intrator</p>"]
    res['body'] = ''.join(html)
    res['status'] = 200

@app.produces('text/plain')
@app.get('/name')
def name(req, res):
    res['body'] = app.name
    res['status'] = 200

@app.produces('application/json')
@app.get('/json')
def json(req, res):
    res['body'] = '{"data": "value", "data2": "value2"}'
    res['status'] = 200

server = Server(5000, app)
server.serve()
