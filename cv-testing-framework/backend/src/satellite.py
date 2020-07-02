
"""
Handle requests related to managing hub satellites.
Exposed At: <host>/api/satellite/..
"""
from flask import Blueprint, jsonify, request
from src.connections import pg_conn # pylint: disable=import-error
from src.my_logger import logger # pylint: disable=import-error
import datetime

app = Blueprint('satellite', __name__)

@app.route('/advertise', methods=['POST'])
def post_satellite_advertise():
    """
    Satellites will advertise themselves by pinging this interface.
    """
    try:
        body = request.get_json()
        # Should we accept a custom satellite host?
        default_host = request.headers.get('x-forwarded-for', request.remote_addr)   
        satellite_host = body.get('satellite_host', default_host)
        satellite_port = body.get('satellite_port')
        satellite_url = f'http://{satellite_host}:{satellite_port}'
        data = body["data"]
        name = body["name"]
        ttl = data['ttl']
        info = data['info']
        with pg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                INSERT INTO public.satellite(satellite_url, name, expires, info) VALUES (%s, %s, %s, %s)
                ON CONFLICT (satellite_url) DO UPDATE SET expires = EXCLUDED.expires, info = EXCLUDED.info
                ''', [satellite_url, name, datetime.datetime.utcnow() + datetime.timedelta(seconds=ttl), info])
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "error", "error": str(e)}), 400

@app.route('/unadvertise', methods=['POST'])
def post_satellite_unadvertise():
    """
    satellites will advertise themselves by pinging this interface.
    """
    try:
        body = request.get_json()
        # Should we accept a custom satellite host?
        default_host = request.headers.get('x-forwarded-for', request.remote_addr)   
        satellite_host = body.get('satellite_host', default_host)
        satellite_port = body.get('satellite_port')
        satellite_url = f'http://{satellite_host}:{satellite_port}'
        with pg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                DELETE FROM public.satellite WHERE satellite_url = %s
                ''', [satellite_url])
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "error", "error": str(e)}), 400

@app.route('/available')
def get_satellite_available():
    """
    Get a list of available satellites.
    """
    try:
        with pg_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM public.satellite WHERE expires <= (NOW() at time zone 'utc')", [])
                sql = '''SELECT * FROM public.satellite'''
                cursor.execute(sql, [])
                rows = cursor.fetchall()
                return jsonify(rows)
    except Exception as e:
        logger.info(str(e))
        return jsonify({"status": "error", "error": str(e)}), 400
