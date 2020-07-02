#
# This file manages visualizations for tests. Rather than the raw /api/results/... routes, these
# are focused on sending back prepared data for graphing, tables, etc. Each route is a custom, parameterized
# 'select' query. This is mainly for use from the frontend application.
#
# The main functionality of this blueprint is using jinja2 to render sql queries, which
# are then run against a test table. This lets us quickly iterate on feature rich (lots of paramaters and processing) queries
# needed for dashboards without needing to use a lot of python. SQL is quite well suited to this sort of task.
#
# Exposed at http://cv-framework.nvidia.com/api/visualize/...
#

from flask import Blueprint, jsonify, session, request, g, make_response
from src.auth import auth_wrap
from src.connections import pg_conn
from psycopg2 import sql
from jinjasql import JinjaSql
from src.queries.VisualizationView import VisualiztionView
from src.scrapers.TestWriter import TestWriter
import importlib

#
# Module globals
#
app = Blueprint('visualize', __name__)
jsql = JinjaSql()


#
# Load all of the queries programatically
#
all_queries = [
  'src.queries.apic',
  'src.queries.apic_overview',
  'src.queries.gfx_overview',
  'src.queries.gfx_perf',
  'src.queries.nightly',
  'src.queries.registered_scrapers',
  'src.queries.simple',
  'src.queries.sql',
  'src.queries.table_layout',
  'src.queries.vrlperf'
]
for module in all_queries:
  importlib.import_module(module)

def merge_qargs_for_jinja(ctx, v):
  """
  Merge query aruments from request into the dictionary of parameters that is passed to jinja for rendering a query.
  """
  for k in request.args:
    val = request.args.get(k)
    # The string 'false' should be a False value.
    if k in v.options:
      if v.options[k]['type'] == 'boolean':
        val = val.lower() != 'false'
    ctx[k] = val

@app.route('visualizations/<string:system>/<string:name>')
def get_all_visualizations(system, name):
    """
    Get all available visualization configurations for a given test.

    Parameters:
    system: string - the name of the test system ('vrl')
    name: string - the name of the test ('shadertest')

    Returns:
    JSON[] of visualization objects with keys:
      - "id" : integer - id of row
      - "view": string - string tag that corresponds to a visualization view.
      - "json_params": JSON - reserved.

    On Error (400)
      {"status": "error", "error": string}
    """
    try:
      with pg_conn() as conn:
        sql = '''
        SELECT test_visualizations.id as id, query_name, query_params, renderer_name, renderer_params from test_visualizations
        JOIN test_meta ON test_meta.id = test_visualizations.test_meta_id
        WHERE test_meta.system = %s AND test_meta.name = %s;
        '''
        with conn.cursor() as cursor:
          cursor.execute(sql, [system, name])
          res = list(cursor)
          return jsonify(res)
    except Exception as e:
      return jsonify({"status": "error", "error": str(e)}), 400


@app.route('available-queries/<string:system>/<string:name>')
def get_all_available_queries(system, name):
    """
    Get all available queries that should work with a given test.

    Parameters:
    system: string - the name of the test system ('vrl')
    name: string - the name of the test ('shadertest')

    Returns:
    JSON[] of visualization objects with keys:
      - "query": string - string tag that corresponds to the query.

    On Error (400)
      {"status": "error", "error": string}
    """
    try:
      with pg_conn() as conn:
        # Use a test writer to get columns in table
        test_writer = TestWriter(system, name, conn=conn)
        res = [{'query': vis.name, 'renderers': vis.renderers}
               for vis in VisualiztionView.visualizations.values() if vis.matches(test_writer.columns)]
        return jsonify(res)
    except Exception as e:
      return jsonify({"status": "error", "error": str(e)}), 400


@app.route("<string:system>/<string:name>/<string:view>")
def get_visualization_route(system, name, view):
    """
    Polymorphic visulization route.

    Given test system, test name, and a "view" name, runs the select sql query associated with "view", on
    the table defined by "system" and "name", and returns the results. Parameters to the query can be provided
    as query paramaters (the string after a url that looks like "?x=123&y=456&some_option=false"). Available options
    to send can be retreieved with the 'get_visualization_params' route below. 

    Returns:
    JSON:  {"data": JSON[] of rows}

    Each row will have keys depending on the columns in the test table.
    """
    v = VisualiztionView.visualizations.get(view)
    if v is None:
        return jsonify({"status": "error", "error": "Unknown view " + view}), 400
    try:
        ctx = {}
        merge_qargs_for_jinja(ctx, v)
        ctx['system'] = system
        ctx['name'] = name
        ctx['test_table'] = system + '.' + name
        ctx['test_table_denormal'] = system + '.' + name + '_denormal'
        query, bind_params = jsql.prepare_query(v.template, ctx)
        with pg_conn(readOnly=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, list(bind_params))
                res = list(cursor)
                return jsonify({
                  "renderers": v.renderers,
                  "data": res
                })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 400


@app.route('<string:system>/<string:name>/<string:view>/params')
@app.route('<string:system>/<string:name>/<string:view>/params/<string:only>')
def get_visualization_params(system, name, view, only=None):
  """
  Get available parameters to a visualization route, as well as possible values for
  those options.
  """
  # Pass in only to only get available params for certain fields.
  only_names = []
  if only:
    only_names = only.split('+')
  v = VisualiztionView.visualizations.get(view)
  if v is None:
    return jsonify({"status": "error", "error": "Unknown view " + view}), 404
  params = []
  try:
    with pg_conn(readOnly=True) as conn:
      with conn.cursor() as cursor:
        for param_name, param_value in v.options.items():
          if only and (param_name not in only_names):
            continue
          if param_value['type'] == 'query':
            ctx = {}
            merge_qargs_for_jinja(ctx, v)
            ctx['system'] = system
            ctx['name'] = name
            ctx['test_table'] = system + '.' + name
            ctx['test_table_denormal'] = system + '.' + name + '_denormal'
            query, bind_params = jsql.prepare_query(param_value['payload'], ctx)
            cursor.execute(query, list(bind_params))
            res = [row['name'] for row in cursor]
            params.append({
              'name': param_name,
              'type': 'query',
              'options': res,
              'optional': param_value['optional'],
              'doc': param_value['doc'],
              'default': param_value['default']
            })
          else:
            params.append({
              'name': param_name,
              **param_value
            })
  except Exception as e:
    return jsonify({"status": "error", "error": str(e)}), 400
  return jsonify({"params": params})
