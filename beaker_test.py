from beaker import Beaker
from beaker import Request
from beaker import Response

app = Beaker('Test App')

@app.get('/simple/endpoint')
def basic_endpoint(req):
    return Response(body='simple endpoint', status=200)

@app.get('/params')
def url_params(req):
    text = "{0} {1}".format(req.args['a'], req.args['b'])
    return Response(body=text, status=200)

@app.get('/vars/<a>/<b>/not/<c>')
def three_vars(req, a, b, c):
    text = '{0} {1} {2}'.format(a, b, c)
    return Response(body=text, status=200)

@app.get('/vars/<a>/rat')
def one_var(req, a):
    text = '{0} rat'.format(a)
    return Response(body=text, status=200)

@app.get('/redirect/<arg>')
def redirection(req, arg):
    return app.redirect(app.url_for('one_var', a=arg), req)

@app.get('/integer/<int:arg>')
def integer_arg(req, arg):
    return Response(body=str(type(arg)), status=200)

def test_arg_type():
    req = Request(path="/integer/6", method="GET")
    res = app.request(req)
    assert res.status == 200
    assert res.body == str(int)

def test_redirect():
    req = Request(path="/redirect/huge", method="GET")
    res = app.request(req)
    assert res.status == 200
    assert res.body == 'huge rat'

def test_simple_endpoint():
    req = Request(path="/simple/endpoint", method="GET")
    res = app.request(req)
    assert res.status == 200
    assert res.body == 'simple endpoint'

def test_url_params():
    req = Request(path="/params", query="a=hello&b=there", method="GET")
    res = app.request(req)
    assert res.status == 200
    assert res.body == 'hello there'

def test_three_vars():
    req = Request(path="/vars/hello/there/not/me", method="GET")
    res = app.request(req)
    assert res.status == 200
    assert res.body == 'hello there me'

def test_one_var():
    req = Request(path="/vars/large/rat", method="GET")
    res = app.request(req)
    assert res.status == 200
    assert res.body == 'large rat'

def test_partial_path():
    req = Request(path="/vars/large", method="GET")
    res = app.request(req)
    assert res.status == 404

def test_no_such_path():
    req = Request(path="/fake/path", method="GET")
    res = app.request(req)
    assert res.status == 404

def test_paths():
    path_a = '/this/is/a/path'
    path_b = '/path/with/trailing/slash/'
    path_b_correct = '/path/with/trailing/slash'
    assert app._list_to_path(app._path_to_list(path_a)) == path_a
    assert app._list_to_path(app._path_to_list(path_b)) == path_b_correct

def test_url_for():
    assert app.url_for('one_var', a=1) == '/vars/1/rat'

if __name__ == '__main__':
    test_arg_type()
    test_paths()
    test_simple_endpoint()
    test_three_vars()
    test_one_var()
    test_no_such_path()
    test_partial_path()
    test_url_params()
    test_url_for()
    test_redirect()
    print "Tests Passed"
