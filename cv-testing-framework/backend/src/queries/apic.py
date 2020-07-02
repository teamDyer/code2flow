from src.visualize import VisualiztionView

# DVSGraph style result viewing for perf trends at the test suite level.
apic = VisualiztionView('apic', ['line-graph', 'bar-chart', 'table'],
                        """
select *, changelist as x,
{% if group %}
  gpu as label, 
{% else %}
  CONCAT("group", ' - ', gpu) as label, 
{% endif %}
{% if subtest %}
  subtest_results -> {{ subtest }} as y
{% else %}
  total_score as y
{% endif %}
from {{ test_table | sqlsafe }}
where true
{% if subtest %}
  and subtest_results ? {{ subtest }}
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
{% if branch %}
  and branch = {{ branch }}
{% endif %}
{% if group %}
  and "group" = {{ group }}
{% else %}
  {% if group_regex %}
    and "group" {% if group_regex_exclude %} not {% endif %} similar to {{ group_regex }}
  {% endif %}
{% endif %}
{% if gpu %}
  and gpu = {{ gpu }}
{% endif %}
order by x desc
{% if limit %}
  limit {{ limit }}
{% endif %}
""")
apic.param_nat('limit', optional=True, default=1000, doc="Limit the number of rows returned to speed up queries.")
apic.param_integer('cl_min', optional=True, doc="Minimum changelist to return results for.")
apic.param_integer('cl_max', optional=True, doc="Maximum changelist to return results for.")
apic.param_column('branch', 'branch', doc="Filter results to a single branch.")
apic.param_string('group_regex', optional=True, doc="Limit the selected group to a regex pattern. This can be used to either select multiple groups at once or to allow cycling through a subset of patterns.")
apic.param_boolean('group_regex_exclude', optional=True, doc="If selected, invert the group_regex criteria.")
apic.param_query('group', '''
select distinct "group" as name from {{ test_table | sqlsafe }} where
{% if branch %}
branch = {{ branch }}
{% else %}
true
{% endif %}
{% if group_regex %}
and "group" {% if group_regex_exclude %} not {% endif %} similar to {{ group_regex }}
{% endif %}
order by name asc
''', optional=True, depends=['branch', 'group_regex'], doc="Filter results to a single test group.")
apic.param_column('gpu', 'gpu', optional=True, doc="Limit results to a single GPU type, (for apics, as reported by VRL).")
apic.param_date('date_min', optional=True, doc="Minimum job start date to return resutls for (inclusive).")
apic.param_date('date_max', optional=True, doc="Maximum job start date to return resutls for (exclusive).")
apic.param_query('subtest', '''
select * from (select distinct jsonb_object_keys(subtest_results) as name from {{ test_table | sqlsafe }} where
{% if branch %} branch = {{ branch }} {% else %} true {% endif %} and {% if group %} "group" = {{ group }} {% else %} true {% endif %}
) as innerTable where name not like '%%_func'
''', optional=True, doc="Filter to a single subtest value (a single APIC), as multiple apics are run per job in VRL. Will not show functional results (subtests that end with _func)", depends=['branch', 'group'])

apic.require(['changelist', 'gpu', 'group', 'total_score', 'subtest_results', 'branch', 'time_start'])