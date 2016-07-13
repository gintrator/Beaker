# Beaker

Put it in a bottle and shake it all up, affectionately named after Flask.

This project is an experiment in building a small full-stack web service. This is mainly an attempt to figure out how something like Flask is implemented by duplicating some of its features.

`server.py` contains a Server class. The server is called `pygi`, pronounced "piggy". It's a very simple web server based on the python `sockets` library. It includes functions to marshall HTTP requests to and from python dictionaries.

## Using Beaker

To use a Server, you must first have something to serve. In `beaker.py`, I've implemented a simple Flask-like service. By use of decorators, you can define which functions response to REST requests at defined endpoints. Beaker supports arguments as part of the url as well. For instance, to define a `/get` endpoint to produce some html, you'd write the following.

### Code Example

```python
from beaker import Beaker
from beaker import Request
from beaker import Response

app = Beaker('Sample App')

@app.get('/get', mimetype='text/html')
def func(req):
  html = "<h1>You've Got Me!</h1>"
  return Response(body=html, status=200)
```

Similarly the decorators `@app.post` and `@app.delete` do what you'd except.

To support arguments, use brackets in the route declaration. Your declared arguments are injected into the handling function when the endpoint is called. URL parameters are marshalled into a Python dictionary and are available at `req.args`.

```Python
@app.get('/person/<name>/<age>')
def person(req, name, age):
  text = "Hello my name is {0} and I am {1} years old.".format(name, age)
  return Response(body=text, status=200)
```

To call this endpoint, put something like this in your browser: `http://localhost:5000/person/bob/23?a=z&z=a`

A response with the text `Hello my name is bob and I am 23 years old.` will be returned. Additionally, with the function `person`, the dict req.args will looks like this: `{'a': 'z', 'z': 'a'}`.

To serve this app, run the following.

```python
from server import Server

port = 5000
server = Server(port, app)
server.serve()
```

You should now be able to ping your endpoints at `http://localhost:5000`.

### Request and Response Objects

Each endpoint function and argument `req` of type `Request` which allow you to inspect the incoming request. To return a response, use the `Response` object. The only necessary fields are `Response.body` and `Response.status`. Since both of these are essentially python dicts with dot notation, the regular dict constructors will work as well. i.e. `res = Response(body='text', status=200)`.

The argument `req` will have the following fields.

```
method  -> REST Verb
path    -> URI
version -> HTTP Version
headers -> Python dict w/ HTTP Headers
body    -> Payload

```

A Response object should be returned frmo an endpoint with the following field filled.

```
body   -> Payload
status -> HTTP Status Code
```
