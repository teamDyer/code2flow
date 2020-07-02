class VisualiztionView:
  """
  Represents a visualization for a test table. A visualization is just a parameterized sql
  query with assoicated parameters. The query is jinja template that takes a dictionary of arguments
  from the frontend.

  Each option in options will be supplied to the param-chooser component on the frontend to create
  a UI dynamically. This means we can create new visualizations without change frontend code.
  New parameter types (new widget types) do require new frontend code, but can then be used in other visualizations.
  """

  visualizations = {}

  def __init__(self, name, renderers, template):
    self.name = name
    self.template = template
    self.renderers = renderers
    self.options = {}
    self.required_columns = []
    VisualiztionView.visualizations[name] = self

  #
  # Set which columns are needed for this view
  #

  def require(self, cols):
    """
    Say which columns are required to use this view on a test
    """
    self.required_columns += cols

  def matches(self, cols):
    """
    Check if this visualization view matches a given set of table columns.
    """
    for c in self.required_columns:
      if c not in cols:
        return False
    return True

  #
  # Adding options to a visualization
  #

  def param_query(self, pname, sql_template, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {
        'type': 'query',
        'payload': sql_template,
        'optional': optional,
        'default': default,
        'doc': doc,
        'depends': depends
    }
    return self

  def param_denormal_column(self, pname, colname, optional=False, default=None, doc=None, depends=[], filter_string='true'):
    return self.param_query(pname, 'select distinct "' + colname + '" as name from {{ test_table_denormal | sqlsafe }} where ' + filter_string + ' order by name asc',
                            optional=optional, default=default, doc=doc, depends=depends)

  def param_column(self, pname, colname, optional=False, default=None, doc=None, depends=[], filter_string='true'):
    return self.param_query(pname, 'select distinct "' + colname + '" as name from {{ test_table | sqlsafe }} where ' + filter_string + ' order by name asc',
                            optional=optional, default=default, doc=doc, depends=depends)

  def param_boolean(self, pname, optional=False, default=False, doc=None, depends=[]):
    self.options[pname] = {'type': 'boolean', 'optional': optional,
                           'default': default, 'doc': doc, 'depends': depends}
    return self

  def param_string(self, pname, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {'type': 'string', 'optional': optional,
                           'default': default, 'doc': doc, 'depends': depends}
    return self

  def param_text(self, pname, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {'type': 'text', 'optional': optional,
                           'default': default, 'doc': doc, 'depends': depends}
    return self

  def param_nat(self, pname, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {'type': 'nat', 'optional': optional,
                           'default': default, 'doc': doc, 'depends': depends}
    return self

  def param_integer(self, pname, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {'type': 'integer', 'optional': optional,
                           'default': default, 'doc': doc, 'depends': depends}
    return self

  def param_integer_range(self, pname, _min, _max, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {
        'type': 'integer_range',
        'min': _min,
        'max': _max,
        'optional': optional,
        'default': default,
        'doc': doc,
        'depends': depends
    }
    return self

  def param_real(self, pname, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {
        'type': 'real',
        'optional': optional,
        'default': default,
        'doc': doc,
        'depends': depends
    }
    return self

  def param_real_range(self, pname, _min, _max, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {
        'type': 'real_range',
        'min': _min,
        'max': _max,
        'optional': optional,
        'default': default,
        'doc': doc,
        'depends': depends
    }
    return self

  def param_date(self, pname, optional=False, default=None, doc=None, depends=[]):
    self.options[pname] = {
        'type': 'date',
        'optional': optional,
        'default': default,
        'doc': doc,
        'depends': depends
    }
    return self
