# Beaker

Put it in a bottle and shake it all up, affectionately named after flask.

This project is an experiment in building a small full-stack web service.

`server.py` contains a Server class. The server is called `pygi`, pronounced "piggy". It's a very simple web server based on the python `sockets` library. It includes functions to marshall HTTP requests to and from python dictionaries.

To use a Server, you must first have something to serve. In `beaker.py`, I've implemented a simple Flask-like service. By use of decorators, you can define which functions response to REST requests at defined endpoints. For instance, to define a `/get` endpoint to produce some html, you'd write the following.

```python
from beaker import Beaker

app = Beaker('Sample App')

@app.produces('text/html')
@app.register('/get', "GET")
def get():
  return "<h1>You've Got Me!</h1>"
```

To serve this app, run the following.

```python
from server import Server

port = 5000
server = Server(port, app)
server.serve()
```

You should now be able to ping your endpoints at `http://localhost:5000`.
