from src.visualize import VisualiztionView

apic = VisualiztionView('gfx_overview', ['line-graph', 'table', 'bar-chart'], """
select exp(avg(ln(total_score + 0.001))) - 0.001 as y, COUNT(*) as num_jobs, jsonb_agg(id) as ids, changelist as x, changelist,
  MIN(total_score) as y_min, MAX(total_score) as y_max, stddev(total_score) as y_stddev,
{% if by_testname %}
  test_name as label
{% else %}
  gpu_name as label
{% endif %}
from {{ test_table_denormal | sqlsafe }}
where total_score != 0
{% if gpu_regex %}
  and gpu_name similar to {{ gpu_regex }}
{% endif %}
{% if testname_regex %}
  and test_name similar to {{ testname_regex }}
{% endif %}
{% if branch %}
  and branch = {{ branch }}
{% endif %}
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
group by changelist,
{% if by_testname %}
  test_name
{% else %}
  gpu_name
{% endif %}
order by x desc
{% if limit %}
  limit {{ limit }}
{% endif %}
""")
apic.param_string('testname_regex', doc="Select which group (apic test name) to average by a regular expression.")
apic.param_string('gpu_regex', doc="Select which gpus (apic test name) to average by a regular expression.")
apic.param_nat('limit', optional=True, default=1000, doc="Limit the number of rows returned to speed up queries.")
apic.param_denormal_column('branch', 'branch', doc="Filter results to a single branch.")
apic.param_boolean('by_group', doc="Show results by group or by GPU.")
apic.param_integer('cl_min', optional=True, doc="Minimum changelist to return results for.")
apic.param_integer('cl_max', optional=True, doc="Maximum changelist to return results for.")
apic.param_date('date_min', optional=True, doc="Minimum job start date to return results for (inclusive).")
apic.param_date('date_max', optional=True, doc="Maximum job start date to return results for (exclusive).")

apic.require(['p4cl_id', 'total_score', 'machine_config_id', 'branch_id', 'time_start'])