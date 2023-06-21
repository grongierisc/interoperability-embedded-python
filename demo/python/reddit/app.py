def demo_app(environ,start_response):
    from io import StringIO
    stdout = StringIO()
    print("Hello world!", file=stdout)
    print(file=stdout)
    h = environ.items()
    for k,v in h:
        print(k,'=',repr(v),type(v), file=stdout)
    start_response("200 OK", [('Content-Type','text/plain; charset=utf-8')])
    return [stdout.getvalue().encode("utf-8")]