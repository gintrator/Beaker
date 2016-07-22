import re
import os.path
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

class Beaker:

    """
    Beaker

    Flask-like functionality
    """

    # Store variables and functions as routes without using a string.
    _VAR_KEY = ('var_key', )
    _FUNC_KEY = ('func_key', )

    _VALID_METHODS = ['GET', 'POST', 'DELETE']
    _HTTP_CODES = {200: '200 OK',
                   400: '400 BAD REQUEST',
                   404: '404 NOT FOUND',
                   500: '500 INTERNAL SERVER ERROR'}
    _VAR_TYPES = {'int': int,
                  'float': float,
                  'str': str}

    def __init__(self, name='default'):
        self.name = name
        
        # self._routes stores a mapping of URL paths to functions.
        # Used to map incoming requests to function.
        self._routes = {}
        
        # self._static stores a mapping of static paths to static resources.
        self._static = {}

        # self._funcs stores a mapping of function names to functions.
        self._funcs = {}

        # self._func_routes stores a mapping of function names to paths.
        # Used to recreate URL's from function names and URL variables.
        self._func_routes = {}
        
        # self._func_vars stores a mapping of function names to its URL variables and types.
        # Used to call an endpoint function with the correct URL variables.
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
            self._funcs[func.__name__] = func
            self._add_route_func(path, method, func.__name__, mimetype)
            return func
        return decorator

    def static(self, path, resource, mimetype='text/plain'):
        self._static[path + '/' + resource] = (resource, mimetype)

    def redirect(self, path, req):
        """
        Redirect this request to the given path.
        """
        req.path = path
        return self.request(req)

    def url_for(self, func_name, **kwargs):
        """
        Find the URL for this function given the variables in kwargs.
        """
        # Mutates this path list if we don't copy - more general _replace_path_var?
        paths = self._func_routes[func_name]
        func_vars = self._func_vars[func_name]
        url_paths = []
        var_index = 0
        for i in range(len(paths)):
            if paths[i] is Beaker._VAR_KEY:
                url_paths.append(str(kwargs[func_vars[var_index][1]]))
                var_index += 1
            else:
                url_paths.append(paths[i])
        return self._list_to_path(url_paths)

    def _add_route_func(self, path, method, func_name, mimetype):
        """
        Recursively breaks down the path into dictionaries, like a filesystem folder structure.
        Stores a mapping to the endpoint function at the end of the path.
        """
        paths = self._replace_path_vars(path, method, func_name)
        self._func_routes[func_name] = paths
        routes = self._routes
        func_signature = (Beaker._FUNC_KEY, method)
        for i in range(len(paths)):
            key = paths[i]
            if key not in routes:
                routes[key] = {}
            routes = routes[key]
        routes[func_signature] = (func_name, mimetype)

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
        func_name, mimetype = routes[func_signature]
        return (func_name, mimetype, func_route)

    def _replace_path_vars(self, path, method, func_name):
        """
        Populates the dictionary self._func_vars this function's URL vars.
        Returns a list representing this path with vars replaced with Beaker._VAR_KEY.
        """
        paths = self._path_to_list(path)
        for i, path_part in enumerate(paths):
            var = self._check_var(path_part)
            if var:
                paths[i] = Beaker._VAR_KEY
                type_func = str
                if ':' in var:
                    type_name, var = var.split(':')
                    if type_name in Beaker._VAR_TYPES:
                        type_func = Beaker._VAR_TYPES[type_name]
                self._func_vars[func_name].append((type_func, var))
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

    def _get_kwargs(self, path, func_route, func_name):
        """
        Find the mapping of function args to values for this endpoint.
        """
        path_list = self._path_to_list(path)
        func_vars = self._func_vars[func_name]
        kwargs = {}
        try:
            for (key, value) in zip(func_vars, filter(lambda e: e not in func_route, path_list)):
                type_func, var = key
                kwargs[var] = type_func(value)
            return kwargs
        except ValueError:
            return None

    def _handle_endpoint_request(self, req):
        """
        Handle calling and returning data from registered endpoint.
        Returns a Response containing the data or not found.
        """
        func_data = self._find_route_func(req.path, req.method)
        if not func_data:
            return Response(status=404, body='Resource not found.', mimetype='text/plain')
        func_name, mimetype, func_route = func_data
        kwargs = self._get_kwargs(req.path, func_route, func_name)
        if kwargs is None:
            return Response(status=400, body='Wrong type in URL variable.', mimetype='text/plain')
        res = self._funcs[func_name](req, **kwargs)
        res.mimetype = mimetype
        if not res.status:
            res.status = 200
        return res
    
    def _handle_static_request(self, req):
        """
        Handle files registered with the self.static method.
        req.path is guaranteed to be in self._static, but not necessarily a valid file.
        Returns a Response containing the file content or not found.
        """
        filename, mimetype = self._static[req.path]
        full_path = os.path.realpath('.') + '/' + filename
        if not os.path.isfile(full_path):
            return Response(status=404, body='File not found.', mimetype='text/plain')
        with open(filename, 'rb') as file:
            static_data = file.read()
        return Response(status=200, body=static_data, mimetype=mimetype)
    
    def _validate_request(self, req):
        """
        Validate request field.
        Returns a string describing failure or None if everything is fine.
        """
        if req.method not in Beaker._VALID_METHODS:
            return 'Invalid HTTP method.'
        if req.query:
            try:
                req.args = {k: v for (k, v) in (var.split('=') for var in req.query.split('&'))}
            except ValueError:
                return 'Malformed URL Parameters.'
        return None
    
    def request(self, req):
        """
        Takes a parameter req of type Request.
        Validates Request and dispatches to appropriate handler.
        Returns a Response object with appropriate fields.
        """
        try:
            is_valid_req = self._validate_request(req)
            if is_valid_req is not None:
                return Response(status=400, body=is_valid_req, mimetype='text/plain')
            if req.path in self._static:
                return self._handle_static_request(req)
            else:
                return self._handle_endpoint_request(req)
        except Exception as e:
            error = "Internal Server Error: {0}.".format(repr(e))
            return Response(status=500, body=error, mimetype='text/plain')
    
    def _parse_env(self, env):
        req = Request()
        req.path = env['PATH_INFO']
        req.method = env['REQUEST_METHOD']
        req.query = env['QUERY_STRING']
        req.args = {}
        req.body = env['wsgi.input'].read()
        return req

    def _wsgi_interface(self, environ, start_response):
        req = self._parse_env(environ)
        res = self.request(req)
        headers = [('Content-Length', str(len(res.body))),
                   ('Content-Type', res.mimetype)]
        start_response(Beaker._HTTP_CODES[res.status], headers)
        return [res.body]


