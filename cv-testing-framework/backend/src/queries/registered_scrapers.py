from src.visualize import VisualiztionView

q = VisualiztionView('registered_scrapers', ['table'],
'''
SELECT * FROM test_meta
JOIN test_scrapers ON test_scrapers.test_meta_id = test_meta.id
WHERE system = {{ system }} AND name = {{ name }}
''')