from functools import wraps
from flask import Blueprint, jsonify, session, request, abort, current_app
import ldap3
import os

app = Blueprint('auth', __name__)

ldap_server = ldap3.Server(host='ldap.nvidia.com', port=389)

is_test = os.getenv('FLASK_ENV') == 'test'

#
# Routes
#

@app.route('status', methods=['POST'])
def status():
    if "username" not in session:
        return jsonify({"status": "logged_out"})
    else:
        return jsonify({
            "status": "logged_in",
            "username": session["username"]
        })

@app.route('login', methods=['POST'])
def login():
    """
    Add session token based on login data
    """

    body = request.get_json(force=True)
    if not body:
        return jsonify("Bad json body"), 400
    if "username" not in body:
        return jsonify("Expected username"), 400
    if "password" not in body:
        return jsonify("Expected password"), 400
    if is_test:
        # Just whitelist a single test user - will not run in production
        if body["username"] == "testuser" and body["password"] == "testpassword":
            session["username"] = "testuser"
        res = jsonify("ok")
        return res
    else:
        try:
            conn = ldap3.Connection(ldap_server, user=(body["username"] + "@nvidia.com"), password=body["password"])
            result = conn.bind()
            if not result:
                return jsonify(conn.result), 400
            # We have validated that username/password combo is good
            session["username"] = body["username"]
            return jsonify("ok")
        except Exception as e:
            print(str(e))
            return jsonify("authentication error"), 400

@app.route('logout', methods=["POST"])
def logout():
    session.pop('username', None)
    return jsonify("ok")

def auth_wrap(f):
    """
    Decorator that requires a user to be logged in for the given route.
    Will return a 403 if the user is not logged in. The frontend should then
    handle the 403 and show the login page.
    """
    @wraps(f)
    def route_prime(*args, **kwargs):
        if "username" not in session:
            return abort(403)
        return f(*args, **kwargs)
    return route_prime
