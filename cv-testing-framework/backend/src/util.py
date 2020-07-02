def escape_sql_like(s):
    return s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_').replace("'", "\\'")

def sql_filter_clause(colname, filterstring):
    """
    Create a string of SQL that can be used to do text searching
    in a SQL Database. The resulting fragment of SQL will end up like
    'WHERE "colname" LIKE %pat1% AND "colname" LIKE %pat2% ...'.
    (No trailing semicolon).
    For each search string in filterstring, where search strings are separated by '+'
    characters. This is a common, url way friendly of specifying a set of strings via HTTP.
    This is meant for our main Postgres database, but should work for MySQL too.

    Returns a new SQL fragment as a string.
    """
    clauses = []
    for term in filterstring.split('+'):
        if term:
            clauses.append("%s LIKE '%s'" % (colname, '%' + escape_sql_like(term) + '%'))
    if not clauses:
        clauses.append('true')
    return (' AND ').join(clauses)