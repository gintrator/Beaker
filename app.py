from server import Server
from beaker import Beaker

port = 5000
app = Beaker("Beaker Application v1.1.")

@app.produces('text/html')
@app.register('/', "GET")
def index():
    html = ["<h1>Welcome to a Beaker app!</h1>",
            "<p>This is a sample beaker application.</p>",
            "<p>It's used to build simple RESTful services.</p>",
            "<p>It's very much like Flask, except that I wrote it.</p>",
            "<p>Check out a <a href='/json'>json endpoint</a></p>",
            "</br>",
            "<p>by Gabriel Intrator</p>"]
    return ''.join(html) 

@app.produces('text/plain')
@app.register('/name', "GET")
def name():
    return app.name

@app.produces('application/json')
@app.register('/json', "GET")
def json():
    return '{"data", "value", "data2": "value2"}'


server = Server(5000, app)
server.serve()
