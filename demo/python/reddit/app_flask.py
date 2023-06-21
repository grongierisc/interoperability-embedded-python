# create a Flask app
from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    """
    Returns a greeting message.
    """
    return 'Hello, World!'

# add a route to say hello to any name
@app.route('/name/<name>')
def hello_name(name):
    """
    Returns a greeting message with a name.
    """
    return f'Hello, {name}!'

# add a post route
@app.route('/', methods=['POST'])
def post():
    """
    Returns a post message.
    """
    payload = request.get_json()
    # return the payload
    return payload
