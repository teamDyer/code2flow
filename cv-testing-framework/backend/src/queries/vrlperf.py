from src.visualize import VisualiztionView

# DVSGraph style result viewing for perf trends at the test suite level.
vrlperf = VisualiztionView('vrlperf', ['line-graph', 'table'],
                        """
select *, changelist as x,
{% if group %}
  gpu as label, 
{% else %}
  CONCAT("group", ' - ', gpu) as label, 
{% endif %}
total_score as y
from {{ test_table | sqlsafe }}
where true
{% if date_min %}
  and
  time_start >= TO_TIMESTAMP({{ date_min }})
{% endif %}
{% if date_max %}
  and
  time_start <= TO_TIMESTAMP({{ date_max }})
{% endif %}
{% if cl_min %}
  and
  CAST(changelist as bigint) >= {{ cl_min }}
{% endif %}
{% if cl_max %}
  and
  CAST(changelist as bigint) <= {{ cl_max }}
{% endif %}
{% if branch %}
  and branch = {{ branch }}
{% endif %}
{% if group %}
  and "group" = {{ group }}
{% endif %}
{% if gpu %}
  and gpu = {{ gpu }}
{% endif %}
order by x desc
{% if limit %}
  limit {{ limit }}
{% endif %}
""")
vrlperf.param_nat('limit', optional=True, default=1000, doc="Limit the number of rows returned to speed up queries.")
vrlperf.param_integer('cl_min', optional=True, doc="Minimum changelist to return results for.")
vrlperf.param_integer('cl_max', optional=True, doc="Maximum changelist to return results for.")
vrlperf.param_column('branch', 'branch', doc="Filter results to a single branch.")
vrlperf.param_column('group', 'group', optional=True, doc="Filter results to a single GG2 group.")
vrlperf.param_column('gpu', 'gpu', optional=True, doc="Limit results to a single GPU type, as reported by VRL.")
vrlperf.param_date('date_min', optional=True, doc="Minimum job start date to return resutls for (inclusive).")
vrlperf.param_date('date_max', optional=True, doc="Maximum job start date to return resutls for (exclusive).")

vrlperf.require(['changelist', 'gpu', 'group', 'total_score', 'branch', 'time_start'])