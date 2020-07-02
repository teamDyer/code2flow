from flask import Flask
from flask_cors import CORS
from requests import get

import src.vrlsubmit
import src.auth
import src.results
import src.dvs
import src.vrl
import src.misc
import src.visualize
import src.machine_monitoring
import src.ops
import src.nvbugs
import src.monitors
import src.ingest
import src.satellite

def create_app():
    # Proper CORS access
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.url_map.strict_slashes = True

    # Add sessions
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
    app.config['SESSION_COOKIE_DOMAIN'] = False

    # Set up subpaths (blueprints in flask jargon)
    app.register_blueprint(src.vrlsubmit.app, url_prefix='/api/vrlsubmit')
    app.register_blueprint(src.auth.app, url_prefix='/api/auth')
    app.register_blueprint(src.results.app, url_prefix='/api/results')
    app.register_blueprint(src.dvs.app, url_prefix='/api/dvs')
    app.register_blueprint(src.vrl.app, url_prefix='/api/vrl')
    app.register_blueprint(src.visualize.app, url_prefix='/api/visualize')
    app.register_blueprint(src.misc.app, url_prefix='/api')
    app.register_blueprint(src.machine_monitoring.app, url_prefix='/api/mm')
    app.register_blueprint(src.ops.app, url_prefix='/api/ops')
    app.register_blueprint(src.nvbugs.app, url_prefix='/api/nvbugs')
    app.register_blueprint(src.monitors.app, url_prefix='/api/monitors')
    app.register_blueprint(src.ingest.app, url_prefix='/api/ingest')
    app.register_blueprint(src.satellite.app, url_prefix='/api/satellite')
    return app

# Expose app for gunicorn
app = create_app()

if __name__ == "__main__":
    print("Running app...")
    app.run('localhost')
