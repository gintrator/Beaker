import re
import collections

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
    
    def __init__(self, name='default'):
        self.name = name
        self._routes = TreeDict()

        self._func_vars = collections.defaultdict(list)
    
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
        def add_routes(routes, paths):
            if len(paths) == 0:
                routes[(Beaker._FUNC_KEY, method)] = (func, mimetype)
            else:
                add_routes(routes[paths[0]], paths[1:])
        add_routes(self._routes, paths)

    def _find_route_func(self, path, method):
        """
        Walks the route tree.
        Return the tuple (func, mimetype, func_route) or (None, None, None).
        """
        paths = self._path_to_list(path)
        routes = self._routes
        func_route = tuple()
        try:
            while len(paths) > 0:
                key = paths.pop(0)
                if key in routes:
                    routes = routes[key]
                    func_route += (key, )
                elif Beaker._VAR_KEY in routes:
                    routes = routes[Beaker._VAR_KEY]
                    func_route += Beaker._VAR_KEY
                else:
                    return None
            func, mimetype = routes[(Beaker._FUNC_KEY, method)]
            return (func, mimetype, func_route)
        except KeyError as e:        
            return None

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

    def _parse_request(self, req):
        """
        Get the method, path, and url parameters from this request.
        """
        path = req['path']
        method = req['method']
        args = {}
        if '?' in path:
            path, args = path.split('?')
            args = {k: v for (k, v) in (var.split('=') for var in args.split('&'))}
        return (method, path, args)

    def _get_kwargs(self, path, func_route, func):
        """
        Find the mapping of function args to values for this endpoint.
        """
        path_list = self._path_to_list(path)
        func_vars = self._func_vars[func.__name__]
        kwargs = {k: v for (k, v) in zip(func_vars, filter(lambda e: e not in func_route, path_list))}
        return kwargs

    def request(self, server_req, server_res):
        req = Request(server_req)
        method, path, args = self._parse_request(req)
        print "Request: {0} {1}".format(method, path)
        func_data = self._find_route_func(path, method)
        if not func_data:
            print "Not found: {0}".format(path)
            return False
        func, mimetype, func_route = func_data
        req.args = args
        kwargs = self._get_kwargs(path, func_route, func)
        res = func(req, **kwargs)
        server_res['body'] = res.body
        server_res['status'] = res.status
        server_res['mimetype'] = mimetype
        return True


app = Beaker('test')

a = '/a/b/c/d'
b = '/a/b/e/d'
app._add_route_func(a, 'GET', lambda: 'a', 'mime')
app._add_route_func(b, 'GET', lambda: 'b', 'mime')

