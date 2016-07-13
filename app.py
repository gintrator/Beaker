from server import Server
from beaker import Beaker
from beaker import Request
from beaker import Response

port = 5001
app = Beaker("Beaker Application v0.1.")

@app.get('/', mimetype='text/html')
def index(req):
    html = ["<h1>Welcome to a Beaker app!</h1>",
            "<p>This is a sample beaker application.</p>",
            "<p>It's used to build simple RESTful services.</p>",
            "<p>It's very much like Flask, except that I wrote it.</p>",
            "<p>Check out a <a href='/json'>json endpoint</a></p>",
            "</br>",
            "<p>by Gabriel Intrator</p>"]
    return Response(body="".join(html), status=200)

@app.get('/name/<arg>', mimetype='text/plain')
def name(req, arg):
    res = """Welcome to {0}.
             Received url argument: {1}
             Received url parameters: {2}
          """.format(app.name, arg, req.args)
    return Response(body=res, status=200)

@app.get('/json', mimetype='application/json')
def json(req):
    json = '{"data": "value", "data2": "value2"}'
    return Response(body=json, status=200)


server = Server(port, app)
server.serve()
