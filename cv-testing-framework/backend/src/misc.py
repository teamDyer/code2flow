import urllib
from flask import Blueprint, jsonify, current_app, url_for

app = Blueprint('misc', __name__)

# Simple site map
# This gives back a response containing available API
# routes, as well as docstrings for their functions.
@app.route("/site-map")
def site_map():
    output = []
    for rule in current_app.url_map.iter_rules():
        try:
            options = {}
            for arg in rule.arguments:
                options[arg] = "[{0}]".format(arg)
            url = urllib.parse.unquote(url_for(rule.endpoint, **options))
            func = current_app.view_functions.get(rule.endpoint)
            if func:
                line = {"func": rule.endpoint,
                        "doc": func.__doc__,
                        "methods": [str(x) for x in rule.methods],
                        "url": url}
                output.append(line)
        except Exception as e:
            # skip rule
            pass
    return jsonify(output)