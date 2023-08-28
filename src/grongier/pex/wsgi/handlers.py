from wsgiref.handlers import BaseHandler
import io
import iris

class IrisHandler(BaseHandler):
    """Handler that's just initialized with streams, environment, etc.

    This handler subclass is intended for synchronous HTTP/1.0 origin servers,
    and handles sending the entire response output, given the correct inputs.

    Usage::

        handler = SimpleHandler(
            inp,out,err,env, multithread=False, multiprocess=True
        )
        handler.run(app)"""

    server_software = "IrisWSGI/0.1"
    wsgi_file_wrapper = None

    def __init__(self,stdin,stdout,stderr,environ,
        multithread=True, multiprocess=False
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.base_env = environ
        self.wsgi_multithread = multithread
        self.wsgi_multiprocess = multiprocess

    def get_stdin(self):
        if not self.stdin:
            return None
        else:
            self.environ["wsgi.input"] = io.BytesIO(self.stdin)
            self.environ["CONTENT_LENGTH"] = str(len(self.stdin))
            return io.BytesIO(self.stdin)


    def get_stderr(self):
        return self.stderr

    def add_cgi_vars(self):
        self.environ.update(self.base_env)

    def _write(self,data):
        iris.cls('Grongier.Service.WSGI').write(data)

    def _flush(self):
        self.stdout.flush()
        self._flush = self.stdout.flush
