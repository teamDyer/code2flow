from src.visualize import VisualiztionView

# Lowest common demoninator view, just a raw table of results.
nightly = VisualiztionView('nightly', ['table'],
"""
{% if denormal %}
select * from {{ test_table_denormal | sqlsafe }}
{% else %}
select * from {{ test_table | sqlsafe }}
{% endif %}
where is_nightly = true
order by time_start desc
{% if limit %}
  limit {{ limit }}
{% endif %}
{% if offset %}
  offset {{ offset }}
{% endif %}
""")
nightly.param_nat('limit', optional=False, doc="Limit the number of rows returned", default=1000)
nightly.param_nat('offset', optional=True, doc="A simple form of pagination. Skips the first offset results, allowing you to 'scroll' through results by incrementing this value.")
nightly.param_boolean('denormal', optional=True, doc="You may want to enable this for some tests to show better looking results.")
nightly.require(['is_nightly'])