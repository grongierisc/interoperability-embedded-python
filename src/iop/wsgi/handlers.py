import os, sys, importlib, urllib.parse
from io import BytesIO

__ospath = os.getcwd()

import iris

os.chdir(__ospath)

enc, esc = sys.getfilesystemencoding(), 'surrogateescape'

rest_service = iris.cls('%REST.Impl')

def get_from_module(app_path, app_module, app_name):

    # Add the path to the application
    if (app_path not in sys.path) :
        sys.path.append(app_path)

    # retrieve the application
    return getattr(importlib.import_module(app_module), app_name)

# Changes the current working directory to the manager directory of the instance.
def goto_manager_dir():
    iris.system.Process.CurrentDirectory(iris.system.Util.ManagerDirectory())

def unicode_to_wsgi(u):
    # Convert an environment variable to a WSGI "bytes-as-unicode" string
    return u.encode(enc, esc).decode('iso-8859-1')

def wsgi_to_bytes(s):
    return s.encode('iso-8859-1')

def write(chunk):
    rest_service._WriteResponse(chunk)

def start_response(status, response_headers, exc_info=None):
    '''WSGI start_response callable'''
    if exc_info:
        try:
            raise exc_info[1].with_traceback(exc_info[2])
        finally:
            exc_info = None

    rest_service._SetStatusCode(status)
    for tuple in response_headers:
        rest_service._SetHeader(tuple[0], tuple[1])
    return write


# Make request to application
def make_request(environ, stream, application, path):

    # Change the working directory for logging purposes
    goto_manager_dir()

    error_log_file = open('WSGI.log', 'a+')
    
    # We want the working directory to be the app's directory
    if (not path.endswith(os.path.sep)):
        path = path + os.path.sep

    #iris.system.Process.CurrentDirectory(path)
    
    # Set up the body of the request
    if stream != '':
        bytestream = stream
    elif (environ['CONTENT_TYPE'] == 'application/x-www-form-urlencoded'):
        bytestream = BytesIO()
        part = urllib.parse.urlencode(environ['formdata'])
        bytestream.write(part.encode('utf-8'))
        bytestream.seek(0)
    else:
        bytestream = BytesIO(b'')

    #for k,v in os.environ.items():
        #environ[k] = unicode_to_wsgi(v)
    environ['wsgi.input'] = bytestream   
    environ['wsgi.errors'] = error_log_file
    environ['wsgi.version']      = (1, 0)
    environ['wsgi.multithread']  = False
    environ['wsgi.multiprocess'] = True
    environ['wsgi.run_once']     = True


    if environ.get('HTTPS', 'off') in ('on', '1'):
        environ['wsgi.url_scheme'] = 'https'
    else:
        environ['wsgi.url_scheme'] = 'http'
    
    # Calling WSGI application
    response = application(environ, start_response)

    error_log_file.close()

    try:
        for data in response:
            if data:
                # (REST.Impl).Write() needs a utf-8 string
                write(data.decode('utf-8'))
            write(b'')
    finally:
        if hasattr(response, 'close'):
            response.close()
