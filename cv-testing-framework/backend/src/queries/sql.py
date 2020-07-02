from src.visualize import VisualiztionView

# Lowest common denominator view, just a raw sql query.
# Some $ bindings are exposed,  but we may just want to let
# a user pass in an entire template. Limited to 100 returned rows.
sqlview = VisualiztionView('sql', [],
                           """{{ sql 
| replace('$table', test_table)
| replace('$system', system)
| replace('$name', name)
| replace('$table_denormal', test_table_denormal)
| replace('%', '%%')
| sqlsafe }}
""")
sqlview.param_text('sql', False, 'select * from $table limit 100',
                   doc="Raw sql to be executed by the backend. Some special variables are also available, such as $table for the current test table, $table_denormal for a denormalized view if it exists, $system for the test system name, and $name for the test name.")
