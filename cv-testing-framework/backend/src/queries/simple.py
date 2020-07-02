from src.visualize import VisualiztionView

# Lowest common demoninator view, just a raw table of results with raw sql filters.
tableview = VisualiztionView('simple', [],
"""
{% if denormal %}
select * from {{ test_table_denormal | sqlsafe }}
{% else %}
select * from {{ test_table | sqlsafe }}
{% endif %}
{% if sql_predicate %}
  where {{ sql_predicate | sqlsafe }}
{% endif %}
order by time_start desc
{% if limit %}
  limit {{ limit }}
{% endif %}
{% if offset %}
  offset {{ offset }}
{% endif %}
""")
tableview.param_nat('limit', optional=False, doc="Limit the number of rows returned", default=1000)
tableview.param_nat('offset', optional=True, doc="A simple form of pagination. Skips the first offset results, allowing you to 'scroll' through results by incrementing this value.")
tableview.param_text('sql_predicate', optional=True, doc="A SQL predicate clause used to filter results. Should be a SQL expression without the preceding 'where' keyword.")
tableview.param_boolean('denormal', optional=True, doc="You may want to enable this for some tests to show better looking results.")
tableview.require(['time_start'])