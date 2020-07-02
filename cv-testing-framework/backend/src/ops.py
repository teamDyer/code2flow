"""
This file handles all the operations related to ops.
Exposed At: <host>/api/ops/..
"""
from urllib.parse import unquote
from flask import Blueprint, jsonify
from src.connections import pg_conn # pylint: disable=import-error
from src.my_logger import logger # pylint: disable=import-error

app = Blueprint('ops', __name__)


@app.route('/<string:team_name>')
def get_ops_details(team_name):
    """get the ops details for the given team on chub.
    :param team_name: name of the team for which ops details are requested
    :type team_name: string
    :return: list of dict objects with the ops info
    :rtype: list
    """
    try:
        rows = ()
        conn = pg_conn()
        with conn.cursor() as cursor:
            sql = '''
            select
            o.name as ops_name, o.wiki, og.name as grp_name, oo.name as owner_name, oo.email, t.name as team
            from ops o, ops_group og, ops_owner oo, teams t
            where o.ownerid = oo.id
            AND o.opsgroupid = og.id
            AND og.teamid = t.id
            AND t.name = %s
            '''
            cursor.execute(sql, [unquote(team_name)])
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        logger.error(e)
        return jsonify("ERROR"), 400


@app.route('/')
def get_all_ops():
    """get the ops information for all the teams on chub
    :return: list of dict containing ops information for all the teams
    :rtype: list
    """
    try:
        rows = ()
        conn = pg_conn()
        with conn.cursor() as cursor:
            sql = '''
            select
            o.name as ops_name, o.wiki, og.name as grp_name, oo.name as owner_name, oo.email, t.name as team
            from ops o, ops_group og, ops_owner oo, teams t
            where o.ownerid = oo.id
            AND o.opsgroupid = og.id
            AND og.teamid = t.id
            '''
            cursor.execute(sql)
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        logger.error(e)
        return jsonify("ERROR"), 400



@app.route('/getallteams')
def get_all_teams():
    """get all the teams name and id
    :return: a list of dict with team name and team id
    :rtype: list
    """
    try:
        conn = pg_conn()
        with conn.cursor() as cursor:
            sql = '''
                SELECT id, name
                FROM teams
            '''
            cursor.execute(sql)
            rows = cursor.fetchall()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        logger.error(e)
        return jsonify("ERROR"), 400
