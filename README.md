# Beaker

Put it in a bottle and shake it all up, affectionately named after Flask. Beaker is a framework to define REST based services.

This project is an experiment in building a small full-stack web service. This is mainly an attempt to figure out how something like Flask is implemented by duplicating some of its features.

`server.py` contains a Server class. The server is called `pygi`, pronounced "piggy". It's a simple web server based on the python `sockets` library. It includes functions to marshall HTTP requests to and from python dictionaries.

Both Beaker and pygi implement the [WSGI](https://www.python.org/dev/peps/pep-0333/) interface. Beaker can be run on with any WSGI compliant server.

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

A response with the text `Hello my name is bob and I am 23 years old.` will be returned. Additionally, within the function `person`, the dict req.args will look like this: `{'a': 'z', 'z': 'a'}`.

To serve this app, run the following.

```python
from server import Server

port = 5000
server = Server(port, app)
server.serve()
```

You should now be able to ping your endpoints at `http://localhost:5000`.

### URL Variables

Implementing URL variables turned out to be harder than I thought. Since they are unknown until the request arrives, it's difficult to dispatch control to the right endpoint. With static routes, a dictionary works great, a (path, method) pair is unique. However, this is not the case when any part of the path may or not be a variable.

Beaker implements a tree-based solution, via a tree of dictionaries. Here's an example. Assume we have the following endpoints: `/top/left`, `/top/right`, `/top/<var>/left`, and `/top/<var>/right`.

When they are registered, they will be parsed into the tree below. the `'func'` and `'url_var'` keys here are placeholders, the actual keys are tuples so that these are still available as path names. Now we can parse an incoming request easily and efficiently. On every next level of the tree, we check first for exact matches, and then for a variable. If the tree below the variables matches the rest of the request, we can keep on going. Once we reach the end of the URL path we just return the function at the last entry, and call it with the correct arguments.

While this is not as fast as dict lookups for static endpoint paths, its decently efficient. It's also a natural way to store things like files/urls, and allows for a simple implementation of url variables.

```
{'top': {'left':  {'func': <function>,
         'right': {'func': <function>,
                   'url_var': {'left':  {'func': <function>,
                               'right': {'func': <function>}}}}}}}
```

### Request and Response Objects

Each endpoint function will have an argument `req` of type `Request` which allow you to inspect the incoming request. To return a response, use the `Response` object. The only necessary fields are `Response.body` and `Response.status`. Since both of these are essentially python dicts with dot notation, the regular dict constructors will work as well. i.e. `res = Response(body='text', status=200)`.

The argument `req` will have the following fields.
| Key     | Description  | Type |
| ------- | ------------ | ---- |
| method  | REST Verb    | str  |
| path    | Request Path | str  |
| args    | Query Args   | dict |
| version | HTTP Version | str  |
| headers | HTTP Headers | dict |
| body    | Payload      | str  |

A Response object should be returned from an endpoint with the following fields filled.
| Key      | Description       | Default    | Type | 
| -------- | ----------------- | ---------- | ---- |
| status   | HTTP Status Code  | 200        | int  |
| body     | Payload           | None       | str  |
| mimetype | Content Type      | text/plain | str  |


