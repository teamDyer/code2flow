from src.visualize import VisualiztionView

# DVSGraph style result viewing for perf trends at the test suite level.
tl= VisualiztionView('table_layout', ['table'],
'''
SELECT is_nullable as optional, udt_name, column_name as name, data_type as type FROM information_schema.columns
WHERE table_schema = {{ system }} AND
        table_name = CONCAT({{ name }}, 
{% if denormal %}
        '_denormal')
{% else %}
        '')
{% endif %}
ORDER BY ordinal_position;
''')
tl.param_boolean('denormal', doc='Show interface for the denormal view. The denormalized view can be accessed in queries as $table_denormal')