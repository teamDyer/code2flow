from src.visualize import VisualiztionView

# DVSGraph style result viewing for perf trends at the test suite level.
# This should work with any testing that follows the gfx standard for test columns
# Todo subtests
apic = VisualiztionView('gfx_perf', ['line-graph', 'bar-chart', 'table'],
                        """
select *, changelist as x,
{% if testname %}
  gpu_name as label, 
{% else %}
  CONCAT(test_name, ' - ', gpu_name) as label, 
{% endif %}
total_score as y
from {{ test_table_denormal | sqlsafe }}
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
{% if build_type %}
  and build_type = {{ build_type }}
{% endif %}
{% if testname %}
  and test_name = {{ testname }}
{% else %}
  {% if testname_regex %}
    and testname_regex {% if testname_regex_exclude %} not {% endif %} similar to {{ testname_regex }}
  {% endif %}
{% endif %}
{% if gpu %}
  and gpu_name = {{ gpu }}
{% endif %}
order by x desc
{% if limit %}
  limit {{ limit }}
{% endif %}
""")
apic.param_nat('limit', optional=True, default=1000, doc="Limit the number of rows returned to speed up queries.")
apic.param_integer('cl_min', optional=True, doc="Minimum changelist to return results for.")
apic.param_integer('cl_max', optional=True, doc="Maximum changelist to return results for.")
apic.param_denormal_column('build_type', 'build_type', doc="Filter results to a single DVS build type.")
apic.param_denormal_column('branch', 'branch', doc="Filter results to a single branch.")
apic.param_string('testname_regex', optional=True, doc="Limit the selected test to a regex pattern. This can be used to either select multiple tests at once or to allow cycling through a subset of patterns.")
apic.param_boolean('testname_regex_exclude', optional=True, doc="If selected, invert the group_regex criteria.")
apic.param_query('testname', '''
select distinct test_name as name from {{ test_table_denormal | sqlsafe }} where
{% if branch %}
branch = {{ branch }}
{% else %}
true
{% endif %}
{% if testname_regex %}
and testname_regex {% if testname_regex_exclude %} not {% endif %} similar to {{ testname_regex }}
{% endif %}
order by name asc
''', optional=True, depends=['branch', 'testname_regex'], doc="Filter results to a single test group.")
apic.param_denormal_column('gpu', 'gpu_name', optional=True, doc="Limit results to a single GPU type, (for apics, as reported by VRL).")
apic.param_date('date_min', optional=True, doc="Minimum job start date to return resutls for (inclusive).")
apic.param_date('date_max', optional=True, doc="Maximum job start date to return resutls for (exclusive).")

apic.require(['p4cl_id', 'branch_id', 'machine_config_id', 'total_score', 'time_start'])