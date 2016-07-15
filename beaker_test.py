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

def test_simple_endpoint():
    req = Request(path="/simple/endpoint", method="GET")
    res = Response()
    app.request(req, res)
    assert res.body == 'simple endpoint'
    assert res.status == 200

def test_url_params():
    req = Request(path="/params?a=hello&b=there", method="GET")
    res = Response()
    app.request(req, res)
    assert res.body == 'hello there'
    assert res.status == 200

def test_three_vars():
    req = Request(path="/vars/hello/there/not/me", method="GET")
    res = Response()
    app.request(req, res)
    assert res.body == 'hello there me'
    assert res.status == 200

def test_one_var():
    req = Request(path="/vars/large/rat", method="GET")
    res = Response()
    app.request(req, res)
    assert res.body == 'large rat'
    assert res.status == 200

def test_paths():
    path_a = '/this/is/a/path'
    path_b = '/path/with/trailing/slash/'
    path_b_correct = '/path/with/trailing/slash'
    assert app._list_to_path(app._path_to_list(path_a)) == path_a
    assert app._list_to_path(app._path_to_list(path_b)) == path_b_correct

if __name__ == '__main__':
    test_paths()
    test_simple_endpoint()
    test_url_params()
    test_three_vars()
    test_one_var()
