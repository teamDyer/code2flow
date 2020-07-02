"""
This file handles all the requests to nvbugs API.
Exposed At: <host>/api/nvbugs/..
"""
import json
from urllib.parse import unquote
import requests
from flask import Blueprint, jsonify, request
from src.my_logger import logger
from src.connections import pg_conn
from src.auth import auth_wrap


app = Blueprint('nvbugs', __name__)

NVBUG_AUTH_TOKEN = 'Basic bnZpZGlhLmNvbVxjb21wdmVyaWY6TnZpZGlhM2QhODk='
NVBUGS_API_ENDPOINT = "https://nvbugsapi.nvidia.com/NVBugsWebServiceApi/api/"
SEARCH_BUGS_ROUTE = "Search/GetBugs?page=1&limit=100"
get_bug_route = "bug/getbug/{}"
DEFAULT_PAYLOAD = [
    {
        "FieldName": "BugAction",
        "FieldValue": "NOT Dev - Closed - Unverified AND NOT Dev - Closed - Verified AND NOT QA - Closed - Unverified AND NOT QA - Closed - Verified"
    },
    {
        "FieldName": "Disposition",
        "FieldValue": "NOT Not a bug"
    },
    {
        "FieldName": "BugSeverity",
        "FieldValue": "NOT 7-Task Tracking"
    }
]

headers = {
    'Content-Type': 'application/json',
    'Authorization': NVBUG_AUTH_TOKEN
}


def payload_item(field_name, field_value):
    """Genereate a payload item
    :param field_name: field name for payload
    :type field_name: string
    :param field_value: field value for payload
    :type field_value: string
    :return: dict with the payload item
    :rtype: list
    """
    return {"FieldName": field_name, "fieldValue": field_value}


def get_bugs_info(payload):
    """Make a request to NVBugs with the passed payload.
    :param payload: payload to make the request.
    :type payload: dict
    :return: json object with bugs info.
    :rtype: list
    """
    url = NVBUGS_API_ENDPOINT + SEARCH_BUGS_ROUTE
    response = requests.post(
        url, headers=headers, data=json.dumps(payload))
    return json.loads(response.text), response.status_code


def get_keywords(team):
    """Get all the NVBUGS Custom keywords associated with a team.
    All the keywords for a team are stored on the CHUB database and
    retreived from there.
    :param team: the name of the team for which the keywords are being retreived.
    :type team: string
    :return: a list of keywords
    :rtype: list
    """
    keywords = []
    try:
        conn = pg_conn()
        with conn.cursor() as cursor:
            sql = '''
                SELECT
                nvbk.name
                FROM nvbugs_keywords nvbk, teams t
                WHERE nvbk.teamid = t.id
                AND t.name = %s'''
            cursor.execute(sql, [unquote(team)])
            rows = cursor.fetchall()
            keywords = [row['name'] for row in rows]
        conn.close()
    except Exception as e:
        logger.error(e)
    return keywords


def get_team_members(team):
    """get a list of all the team members associated with a team.
    The team members info is on CHUB database.
    :param team: The team name.
    :type team: string
    :return: list of team members name
    :rtype: list
    """
    team_members = []
    try:
        conn = pg_conn()
        with conn.cursor() as cursor:
            sql = '''
                SELECT
                oo.name
                FROM ops_owner oo, teams t
                WHERE oo.teamid = t.id
                AND t.name = %s'''
            cursor.execute(sql, [unquote(team)])
            rows = cursor.fetchall()
            team_members = [row['name'] for row in rows]
        conn.close()
    except Exception as e:
        logger.error(e)
    return team_members


def generate_payload(params):
    """generate a payload based on the parameters passed from the url query parameter.
    :param params: query string parameters
    :type params: dict
    :return: payload for NVBUGs api
    :rtype: dict
    """
    payload = []
    try:
        for field_name in params:
            field_value = params[field_name]
            payload.append(payload_item(field_name, field_value))
        for item in DEFAULT_PAYLOAD:
            payload.append(item)
    except Exception as e:
        logger.error(e)
    return payload


@app.route('/with-keywords/<string:team>')
def get_bugs_with_keywords(team):
    """Get all the bugs which contains the teams keywords.
    :param team: team name for which the bugs are being retrieved
    :type team: string
    :return: list of dict object with the bug details
    :rtype: list
    """
    bugs = []
    try:
        # get the query parameters
        params = request.args
        # get all nvbugs keywords for the team
        keywords = get_keywords(team)
        if keywords:
            # update the params with keywords
            payload_params = dict((key, params[key]) for key in params)
            payload_params['CustomKeyword'] = ' OR '.join(keywords)
            # generate the payload for nvbugs API
            payload = generate_payload(payload_params)
            logger.info(str(payload))
            # make a reruest to nvbugs API
            data, status_code = get_bugs_info(payload)
            if status_code == 200:
                for item in data['ReturnValue']:
                    bug = {}
                    bug['Synopsis'] = item['Synopsis']
                    bug['BugId'] = item['BugId']
                    bug['BugAction'] = item['BugAction']
                    bug['CustomKeyword'] = item['CustomKeyword']
                    bugs.append(bug)
                return jsonify(bugs), 200
            else:
                return jsonify("Unable to make an nvbug api call")
        else:
            return jsonify(bugs)
    except Exception as e:
        logger.error(e)
        return jsonify("ERROR"), 400


@app.route('/without-keywords/<string:team>')
def get_bugs_without_keywords(team):
    """Get all the bugs which contains the teams members and does not have keywords.
    :param team: team name for which the bugs are being retrieved
    :type team: string
    :return: list of dict object with the bug details
    :rtype: list
    """
    bugs = []
    try:
        # get the query parameters
        params = request.args
        # get all nvbugs requesters from the team
        requesters = get_team_members(team)
        # get all keywords for the team
        keywords = get_keywords(team)
        # update the params with requesters
        payload_params = dict((key, params[key]) for key in params)
        payload_params['BugRequesterFullName'] = ' OR '.join(requesters)
        if keywords:
            payload_params['CustomKeyword'] = 'NOT '+' AND NOT '.join(keywords)
        # generate the payload for nvbugs API
        payload = generate_payload(payload_params)
        logger.info(str(payload))
        # make a reruest to nvbugs API
        data, status_code = get_bugs_info(payload)
        if status_code == 200:
            for item in data['ReturnValue']:
                bug = {}
                bug['Synopsis'] = item['Synopsis']
                bug['BugId'] = item['BugId']
                bug['BugAction'] = item['BugAction']
                bug['CustomKeyword'] = item['CustomKeyword']
                bugs.append(bug)
            return jsonify(bugs), 200
        else:
            return jsonify("Unable to make an nvbug api call")
        # return the result
    except Exception as e:
        logger.error(e)
        return jsonify("ERROR"), 400


# @app.route('/get_bug/<string:bug_id>')
def get_bug_details(bug_id):
    """Make a request to NVBugs with the bug id.
    :param bug_id: id of the bug to fetch the info.
    :type bug_id: string
    :return: json object with bugs info.
    :rtype: dict
    """
    try:
        url = NVBUGS_API_ENDPOINT + get_bug_route.format(bug_id)
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        if data['TotalCount'] != 0:
            synopsis = data['ReturnValue']['Synopsis']
            bug_action = data['ReturnValue']['BugAction']['Value']
            return {'Synopsis':synopsis, 'BugAction':bug_action}, response.status_code
        else:
            return jsonify("Bug Not Found"), 404
    except Exception as e:
        print(str(e))
        return jsonify("ERROR"), 400


def get_team_id(team):
    """Get the team id for the given team
    :param team: team name
    """
    team_id = None
    try:
        conn = pg_conn()
        with conn.cursor() as cursor:
            sql = """SELECT id
                    FROM teams
                    WHERE name = %s"""
            cursor.execute(sql, [team])
            rows = cursor.fetchall()
        if len(rows) > 0:
            team_id = rows[0]['id']
        conn.close()
    except Exception as err:
        print("Error:{}".format(str(err)))
    return team_id


@app.route('/add_bug/', methods=['POST'])
@auth_wrap
def add_bug_to_hub():
    """add bug to the hub dictonary
    """
    keys = ['bugid', 'team']
    try:
        if request.json is None:
            raise Exception("No Payload")
        else:
            if not all(key in request.json.keys() for key in keys):    
                raise Exception("Incorrect Payload Format")
            request_data = request.json
            bug_id = request_data['bugid']
            team = request_data['team']
            #Check if the bugid is an actual bug
            data, status_code = get_bug_details(bug_id)
            if status_code == 404:
                return data, 404
            if status_code == 400:
                return data, 400
            if status_code == 200:
                conn = pg_conn()
                with conn.cursor() as cursor:
                    team_id = get_team_id(team)
                    sql = """INSERT INTO bugs(id, team_id)
                            VALUES(%s, %s) ON CONFLICT DO NOTHING"""
                    cursor.execute(sql, [bug_id, team_id])
                conn.commit()
                conn.close()
                return jsonify("bug added to c-hub"), 200
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route('/remove_bug/', methods=['POST'])
@auth_wrap
def remove_bug_from_hub():
    """remove bug from hub db
    """
    keys = ['bugid', 'team']
    try:
        if request.json is None:
            raise Exception("No Payload")
        else:
            if not all(key in request.json.keys() for key in keys):    
                raise Exception("Incorrect Payload Format")    
            request_data = request.json
            bug_id = request_data['bugid']
            team = request_data['team']
            conn = pg_conn()
            with conn.cursor() as cursor:
                team_id = get_team_id(team)
                #delete the bug from hub
                sql = """DELETE FROM bugs
                        WHERE id=%s
                        AND team_id=%s"""
                cursor.execute(sql, [bug_id, team_id])
                rows = cursor.rowcount
            conn.commit()
            if rows:
                return jsonify("bug removed from hub"), 200
            else:
                return jsonify("bug not found on the hub watch list"), 200
    except Exception as e:
        return jsonify(error=str(e)), 400


@app.route('/get_user_added_bugs/<string:team>')
def get_user_added_bugs(team):
    """
    Get all the bugs from the hub db for a given team
    :param team: team name
    """
    try:
        conn = pg_conn()
        with conn.cursor() as cursor:
            team_id = get_team_id(team)
            sql = """SELECT * FROM bugs
                    WHERE platform='nvbugs'
                    AND team_id = %s"""
            cursor.execute(sql, [team_id])
            rows = cursor.fetchall()
        bug_ids = []
        for row in rows:
            bug_ids.append(row['id'])
        #get bug info
        bug_details = []
        for id in bug_ids:
            data, status_code = get_bug_details(id)
            data['BugId'] = id
            data['CustomKeyword'] = "user_added"
            bug_details.append(data)
        return jsonify(bug_details), 200
    except Exception as e:
        print(str(e))
        return jsonify("ERROR"), 400
