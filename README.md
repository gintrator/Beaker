# Beaker

Put it in a bottle and shake it all up, affectionately named after [Flask](http://flask.pocoo.org). Beaker is a framework to define REST based services.

The main Beaker class is implemented in `beaker.py` and its tests in `beaker_test.py`.

`server.py` contains a Server class. The server is called `pygi`, pronounced "piggy". It's a simple web server based on the python `sockets` library.

There is a sample Beaker app in `app.py` defining endpoints that demonstrate available features.

Both Beaker and pygi implement the [WSGI](https://www.python.org/dev/peps/pep-0333/) interface. Beaker can be run on with any WSGI compliant server.

## Feature Overview

Most features are implementations of things offered in Flask. These features include...

- Route declaration via function decorators.
- Support for URL variables in routes.
- URL Variable types and filters.
- Static routes.
- Request redirection and URL building.
- Error handling.
- WSGI compliant, and a WSGI server to boot.
- Test suite.

This project is an experiment in building a small full-stack web service framework (i.e. server -> framework -> app). This is mainly an attempt to figure out how something like Flask is implemented by duplicating some of its features.

## Simple Route

This snippet defines an endpoint at `/get` that prodoces some HTML.

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

## Static Routes

Declare static resources using the `app.static(path, resource, mimetype='text/plain')` method. Here's a snippet to declare a static CSS file at `/static/style.css`.

```python
app.static('static', 'style.css', mimetype='text/css')
```

## Route Variables and Parameters
To use URL variables, use brackets in the route declaration. Your declared arguments are injected into the handling function when the endpoint is called. URL parameters are marshalled into a Python dictionary and are available at `req.args`.

```Python
@app.get('/person/<name>/<age>')
def person(req, name, age):
    text = "Hello my name is {0} and I am {1} years old.".format(name, age)
    return Response(body=text, status=200)
```

To call this endpoint, put something like this in your browser: `http://localhost:5000/person/bob/23?a=z&z=a`

A response with the text `Hello my name is bob and I am 23 years old.` will be returned. Additionally, within the function `person`, the dict req.args will look like this: `{'a': 'z', 'z': 'a'}`.


## Redirection and Generating URLs

Redirect to other endpoints by returning `app.redirect(path, req)` instead of a Response. To redirect to a path that might contain variables, create URLs using `app.url_for(func_name, **kwargs)`. For instance, to generate a URL for the endpoint defined in the section above, call `app.url_for('person', name='bob', age='23')` to generate the URL `/person/bob/23`. Putting this all together, we can write the following endpoint.

```python
@app.get('/makeperson')
def make_person(req):
    age = '25'
    name = 'Eve'
    return app.redirect(app.url_for('person', name=name, age=age), req)
```

Now, a GET request to `/makeperson` will return a Response with the text `Hello my name is Eve and I am 25 years old.`.

## Route Filters

Beaker supports filters for URL variables. You can define a type for each URL variable when you declare a route, where the default type is 'str'. For instance, if you register the route `app.get('/<int:arg>')`, when the decorated endpoint is called, `arg` will be an int.

You can also define your own filters by calling `app.add_filter(filter_name, filter_func)`. In the following example, we register a filter called 'list' that expects a URL variable that is comma separated. Inside the function `filtered`, var is of type list, and contains the content of the requested URL.

```Python
app.add_filter('list', lambda var: var.split(','))

@app.get('/<list:var>')
def filtered(req, var):
    for e in var:
        print e
    return Response(body='OK', status=200)
```

A request to `/strings,in,list` will print the strings 'strings', 'in', and 'list' to stdout.


## Error Handling

By default, Beaker returns simple errors for 404, 400, and 500 statuses. To define your own error handling functions, use the `error` decorator. 

The decorated function must take an argument `error`, a string describing the error. You can can also declare the mimetype, the default is `text/plain`.

Make sure that the response contains the correct status code, or things will get confusing.

```python
@app.error(404, mimetype='text/html')
def four_oh_four(error):
    html_error = '<h1>404</h1><p>{0}</p>'.format(error)
    return Response(status=404, body=html_error)
```

## WSGI Server

To serve this app, run the following.

```python
from server import Server

port = 5000
server = Server(port, app)
server.serve()
```

You should now be able to ping your endpoints at `http://localhost:5000`.

## URL Variables Implementation

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

## Request and Response Objects

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


