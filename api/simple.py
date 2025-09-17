def app(environ, start_response):
    """Minimal test handler"""
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    return [b'Hello from Vercel! Django deployment test.']