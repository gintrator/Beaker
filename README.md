# Beaker

Put it in a bottle and shake it all up, affectionately named after flask.

This project is an experiment in building a small full-stack web service.

`server.py` contains a Server class. The server is called `pygi`, pronounced "piggy". It's a very simple web server based on the python `sockets` library. It includes functions to marshall HTTP requests to and from python dictionaries.

## Using Beaker

To use a Server, you must first have something to serve. In `beaker.py`, I've implemented a simple Flask-like service. By use of decorators, you can define which functions response to REST requests at defined endpoints. For instance, to define a `/get` endpoint to produce some html, you'd write the following.

### Code Example

```python
from beaker import Beaker

app = Beaker('Sample App')

@app.produces('text/html')
@app.get('/get')
def func(req, res):
  res['body'] = "<h1>You've Got Me!</h1>"
  res['status'] = 200
```

Similarly the decorators `@app.post` and `@app.delete` do what you'd except.

To serve this app, run the following.

```python
from server import Server

port = 5000
server = Server(port, app)
server.serve()
```

You should now be able to ping your endpoints at `http://localhost:5000`.

### Request and Response Argument

Each endpoint function has two arguments, `req` and `res` which allow you to inspect the incoming request and set the data in the outgoing response.

The request argument `req` will be a python dictionary with the following fields.

```
method  -> REST Verb
path    -> URI
version -> HTTP Version
headers -> Python dict w/ HTTP Headers
body    -> Payload

```

The response argument `res` will be a python dictionary with the following fields that should be filled accordingly.

```
body   -> Payload
status -> HTTP Status Code
```
