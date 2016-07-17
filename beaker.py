import re
from collections import defaultdict
import pprint

class DotDict(dict):
    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delattr__

class Request(DotDict):
    """
    Request object req will have:
    method  -> REST Verb
    path    -> URI
    version -> HTTP Version
    body    -> payload
    """
    pass

class Response(DotDict):
    """
    Response object res will have:
    body   -> payload
    status -> HTTP Status Code
    """
    pass

class TreeDict(dict):
    """
    Similar to a default dict, but arbitrarily recursive.
    """
    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, TreeDict())

class Beaker:

    """
    Beaker

    Flask-like functionality
    """

    # Need a way to store variables and functions in the path dictionary without using a string.
    _VAR_KEY = ('var_key', )
    _FUNC_KEY = ('func_key', )
    HTTP_CODES = {200: '200 OK',
                  400: '400 BAD REQUEST',
                  404: '404 NOT FOUND',
                  500: '500 INTERNAL SERVER ERROR'}

    def __init__(self, name='default'):
        self.name = name
        self._routes = TreeDict()
        self._func_vars = defaultdict(list)

    def __call__(self, *args, **kwargs):
        return self._wsgi_interface(*args, **kwargs)

    def get(self, path, mimetype='text/plain'):
        return self.register(path, "GET", mimetype)

    def post(self, path, mimetype='text/plain'):
        return self.register(path, "POST", mimetype)

    def delete(self, path, mimetype='text/plain'):
        return self.register(path, "DELETE", mimetype)

    def register(self, path, method="GET", mimetype='text/plain'):
        def decorator(func):
            self._add_route_func(path, method, func, mimetype)
            return func
        return decorator

    def _add_route_func(self, path, method, func, mimetype):
        """
        Recursively breaks down the path into dictionaries, like a filesystem folder structure.
        Stores a mapping to the endpoint function at the end of the path.
        """
        paths = self._replace_path_vars(path, method, func)
        routes = self._routes
        func_signature = (Beaker._FUNC_KEY, method)
        for i in range(len(paths)):
            routes = routes[paths[i]]
        routes[func_signature] = (func, mimetype)

    def _find_route_func(self, path, method):
        """
        Walks the route tree.
        Return the tuple (func, mimetype, func_route) or None.
        """
        paths = self._path_to_list(path)
        routes = self._routes
        func_route = tuple()
        func_signature = (Beaker._FUNC_KEY, method)
        for i in range(len(paths)):
            key = paths[i]
            if key in routes:
                routes = routes[key]
                func_route += (key, )
            elif Beaker._VAR_KEY in routes:
                routes = routes[Beaker._VAR_KEY]
                func_route += Beaker._VAR_KEY
            else:
                return None
        if func_signature not in routes:
            return None
        func, mimetype = routes[func_signature]
        return (func, mimetype, func_route)

    def _replace_path_vars(self, path, method, func):
        """
        Populates the dictionary self._func_vars
        Keys: func.__name__
        Values: List of this function's URL variables in order.

        Returns a list representing this path with vars replaced with Beaker.VAR_KEY.
        """
        paths = self._path_to_list(path)
        for i, path_part in enumerate(paths):
            var = self._check_var(path_part)
            if var:
                paths[i] = Beaker._VAR_KEY
                self._func_vars[func.__name__].append(var)
        return paths

    def _check_var(self, path_part):
        """
        Check if this part of the path is a variable.
        Anything surrounding by angle brackets '<var>' is a variable.
        """
        match = re.search('<(.*)>', path_part)
        return match.group(1) if match else None

    def _path_to_list(self, path):
        """
        Convert a path string to a path list.
        """
        return path.strip('/').split('/')

    def _list_to_path(self, path_list):
        """
        Convert a path list to a path string.
        """
        path_list = [''] + path_list
        return '/'.join(path_list)

    def _parse_env(self, env):
        req = Request()
        req.path = env['PATH_INFO']
        req.method = env['REQUEST_METHOD']
        req.query = env['QUERY_STRING']
        req.args = {}
        return req

    def _get_args(self, query):
        args = {}
        if query:
            args = {k: v for (k, v) in (var.split('=') for var in query.split('&'))}
        return args

    def _get_kwargs(self, path, func_route, func):
        """
        Find the mapping of function args to values for this endpoint.
        """
        path_list = self._path_to_list(path)
        func_vars = self._func_vars[func.__name__]
        kwargs = {k: v for (k, v) in zip(func_vars, filter(lambda e: e not in func_route, path_list))}
        return kwargs

    def request(self, req):
        func_data = self._find_route_func(req.path, req.method)
        if not func_data:
            return Response(status=404, body='Resource not found.', mimetype='text/plain')
        func, mimetype, func_route = func_data
        req.args = self._get_args(req.query)
        kwargs = self._get_kwargs(req.path, func_route, func)
        res = func(req, **kwargs)
        res.mimetype = mimetype
        if not res.status:
            res.status = 200
        return res

    def _wsgi_interface(self, environ, start_response):
        req = self._parse_env(environ)
        res = self.request(req)
        headers = [('Content-Length', str(len(res.body))),
                   ('Content-Type', res.mimetype)]
        start_response(Beaker.HTTP_CODES[res.status], headers)
        return [res.body]


