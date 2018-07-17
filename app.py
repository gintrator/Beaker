from server import Server
from wsgiref.simple_server import make_server
from beaker import Beaker
from beaker import Request
from beaker import Response

port = 5000
app = Beaker("Beaker Application v0.1.")

@app.error(404, mimetype='text/html')
def four_oh_four(error):
    html_error = '<h1>404</h1><p>{0}</p>'.format(error)
    return Response(status=404, body=html_error)

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

@app.get('/int/<int:a>')
def intme(req, a):
    assert type(a) == int
    return Response(body='ok', status=200)

@app.get('/name/<arg>', mimetype='text/plain')
def name(req, arg):
    res = """
          Welcome to {0}.
          Received url argument: {1}
          Received url parameters: {2}
          """.format(app.name, arg, req.args)
    return Response(body=res, status=200)

@app.get('/json', mimetype='application/json')
def json(req):
    json = '{"data": "value", "data2": "value2"}'
    return Response(body=json, status=200)

@app.get('/hello')
@app.get('/two/<a>/<b>')
def two(req, a='a', b='b'):
    text = "{0} {1}".format(a, b)
    return Response(body=text, status=200)


@app.get('/<a>/<b>/<c>/<d>')
def many(req, **args):
    text = "{0}".format(args)
    return Response(body=text, status=200)

@app.get('/dict/<list:var>')
def filter_dict(req, var):
    print type(var)
    print (var)
    return Response(body='OK', status=200)


@app.post('/post')
def posted(req):
    print req.body.read()
    return Response(body='got post', status=200)

if __name__ == '__main__':
    use_wsgi_ref = False
    if use_wsgi_ref:
        httpd = make_server('', port, app)
        httpd.serve_forever()
    else:
        server = Server(port, app)
        server.serve()

