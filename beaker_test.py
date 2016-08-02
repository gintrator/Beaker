from beaker import Beaker
from beaker import Request
from beaker import Response

class Tester:

    def __init__(self):
        self.results = {}
        self.tests = []
        self.failed = []

    def test(self, func):
        def test_runner():
            try:
                func()
                self.results[func.__name__] = 'PASSED'
            except AssertionError as e:
                self.failed.append(func.__name__)
                self.results[func.__name__] = e
        self.tests.append(test_runner)
        return test_runner

    def run(self):
        for test in self.tests:
            test()
        if len(self.failed) > 0:
            print '{0}/{1} Tests Failed'.format(len(self.failed), len(self.tests))
            print 'Failed Tests: ' + ' '.join(self.failed)
        else:
            print '{0} Tests Passed'.format(len(self.tests))
        print '-----------------------'
        for test in self.results:
            print '{0}: {1}'.format(test, self.results[test])

tester = Tester()

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

app.add_filter('list', lambda var: var.split(','))

@app.get('/list/<list:var>')
def list_me(req, var):
    text = '/'.join(var + [str(type(var))])
    return Response(body=text, status=200)

@app.error(404)
def four(error):
    return Response(status=404, body='Hit the 404 handler.')

app.static('/static', 'beaker.py')

@tester.test
def test_static_resource():
    req = Request(path="/static/beaker.py", method="GET")
    res = app.request(req)
    with open('beaker.py', 'rb') as beaker_file:
        beaker_source = beaker_file.read()
    assert res.status == 200, 'Status code not 200.'
    assert res.body == beaker_source, 'Static content is incorrect.'

@tester.test
def test_error_handler():
    req = Request(path="/lsdasdads", method="GET")
    res = app.request(req)
    assert res.status == 404, 'Status code not 404.'
    assert res.body == 'Hit the 404 handler.', 'Error body is incorrect.'

@tester.test
def test_filter():
    req = Request(path="/list/a,b,c", method="GET")
    res = app.request(req)
    a, b, c, filtered_type = res.body.split('/')
    assert res.status == 200, 'Status code not 200.'
    assert a == 'a', 'First argument wrong, not a.'
    assert b == 'b', 'Second argument wrong, not b.'
    assert a == 'a', 'Third argument wrong, not c.'
    assert filtered_type == str(list), 'Filter type wrong.'

@tester.test
def test_arg_type():
    req = Request(path="/integer/6", method="GET")
    res = app.request(req)
    assert res.status == 200, 'Status code not 200.'
    assert res.body == str(int), 'Body is not of type int.'

@tester.test
def test_redirect():
    req = Request(path="/redirect/huge", method="GET")
    res = app.request(req)
    assert res.status == 200, 'Status code not 200.'
    assert res.body == 'huge rat', 'Body is not "huge rat".'

@tester.test
def test_simple_endpoint():
    req = Request(path="/simple/endpoint", method="GET")
    res = app.request(req)
    assert res.status == 200, 'Status code not 200.'
    assert res.body == 'simple endpoint', 'Body is not "simple endpoint".'

@tester.test
def test_url_params():
    req = Request(path="/params", query="a=hello&b=there", method="GET")
    res = app.request(req)
    assert res.status == 200, 'Status code not 200.'
    assert res.body == 'hello there', 'Body is not "hello there".'

@tester.test
def test_three_vars():
    req = Request(path="/vars/hello/there/not/me", method="GET")
    res = app.request(req)
    assert res.status == 200, 'Status code not 200.'
    assert res.body == 'hello there me', 'Body is not "hello there me".'

@tester.test
def test_one_var():
    req = Request(path="/vars/large/rat", method="GET")
    res = app.request(req)
    assert res.status == 200, 'Status code not 200.'
    assert res.body == 'large rat', 'Body is not "large rat".'

@tester.test
def test_partial_path():
    req = Request(path="/vars/large", method="GET")
    res = app.request(req)
    assert res.status == 404, 'Status code not 404.'

@tester.test
def test_no_such_path():
    req = Request(path="/fake/path", method="GET")
    res = app.request(req)
    assert res.status == 404, 'Status code not 404.'

@tester.test
def test_paths():
    path_a = '/this/is/a/path'
    path_b = '/path/with/trailing/slash/'
    path_b_correct = '/path/with/trailing/slash'
    assert app._list_to_path(app._path_to_list(path_a)) == path_a, 'Incorrect path.'
    assert app._list_to_path(app._path_to_list(path_b)) == path_b_correct, 'Incorrect path.'

@tester.test
def test_url_for():
    assert app.url_for('one_var', a=1) == '/vars/1/rat', 'Incorrect url construction.'

@tester.test
def test_invalid_url_query():
    req = Request(path="/simple/endpoint", query='a=g&g', method="GET")
    res = app.request(req)
    assert res.status == 400, 'Invalid URL parameters not caught.'

@tester.test
def test_invalid_url_query():
    req = Request(path="/simple/endpoint", method="PUTDELETE")
    res = app.request(req)
    assert res.status == 400, 'Invalid HTTP method not returned as invalid.'

if __name__ == '__main__':
    tester.run()
