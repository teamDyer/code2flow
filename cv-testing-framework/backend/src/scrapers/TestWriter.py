# This class is responsible for validating result data before it is
# inserted into the database.

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from src.connections import pg_conn
from src.scrapers.normalizer import normalize_branch, normalize_gpu, normalize_p4, normalize_machine, normalize_test, normalize_subtests, normalize_user

# Allow for changing names in a backwards compatible way.
# Both old an new names will work.
ALIASES = {
    "gpu_name": "gpu",
    "cpu_name": "cpu",
    "machine_name": "machine",
    "os_name": "os",
    "job_time_start": "time_start",
    "job_time_stop": "time_stop",
    "job_is_nightly": "is_nightly",
    "hd_space_mb": "hd_space",
    "uut_build_type": "build_type",
    "uut_branch": "branch",
    "hd_space_mb": "hd_space",
    "gpu_ram_mb": "gpu_ram",
    "cpu_ram_mb": "cpu_ram",
    "gpu_vbios": "vbios",
    "sw_changelist": "commit_id",
    "cpu_speed_ghz": "cpu_speed",
    "display_type": None
}

def denormalize_columns(cols):
    """
    Expand some select "id" columns that index into another table into their
    denormal form. Works recursively. This is a form of mix and match denormalization.
    This lets us map an internal representation (normalized) to the external interface
    (denormalized).
    Example: (internal)['p4cl_id', 'branch_id', 'some_col'] ->
             (external keys)['changelist', 'branch', 'build', 'some_col']
    """
    from_arr = []
    to_arr = cols
    while to_arr != from_arr:
        from_arr = to_arr
        to_arr = []
        for c in from_arr:
            if c == 'branch_id':
                to_arr += ['branch', 'build_type']
            elif c == 'machine_config_id':
                to_arr += ['machine', 'gpu_id', 'cpu', 'cpu_speed', 'os', 'os_build', 'cpu_ram']
            elif c == 'gpu_id':
                to_arr += ['gpu', 'chip_arch', 'vbios', 'gpu_ram']
            elif c == 'p4cl_id':
                to_arr += ['commit_id']
            elif c == 'subtest_set_id':
                to_arr += ['subtests']
            elif c == 'user_id':
                to_arr += ['job_user']
            elif c == 'test_id':
                to_arr += ['test_name']
            elif c == 'blob':
                pass # ignore blob column - it is for pooling optional extra data
            else:
                to_arr.append(c)
        # Remove duplicates from current denormalized array
        to_arr = list(dict.fromkeys(to_arr))
    return to_arr

class TestWriter:
    """
    Use an instance of this class to write test data to a given test table.
    """

    def __init__(self, test_system, test_name, conn=None):
        self.test_system = test_system
        self.test_name = test_name
        self.connection = conn or pg_conn()
        self._clear_memo()

        # Get the columns of the tests corresponding output table.
        with self.connection.cursor() as cursor:
            cursor.execute("""
            SELECT column_name, is_nullable FROM information_schema.columns
            WHERE table_schema = %s AND
                  table_name = %s
            ORDER BY ordinal_position;
            """, [self.test_system, self.test_name])
            raw_results = list(cursor)
            cols = []
            all_cols = map(lambda row: row["column_name"], raw_results)
            for col in all_cols:
                if col in ['id']:
                    continue
                cols.append(col)
            self.columns = cols
            self.optional_cols = {}
            for row in raw_results:
                # Yes, instead of a boolean, somehow the string 'NO' is returned.
                if row["is_nullable"] and row["is_nullable"] != 'NO':
                    self.optional_cols[row["column_name"]] = True
            # Generate denormalized columns
            self.denormalized_columns = denormalize_columns(cols)
            # Create SQL fragment for inserting columns
            self._columns_sql = '(' + (', ').join(['"%s"' % c for c in cols]) + ')'
            # Build final insert query
            self._insert_sql = f'INSERT INTO "{self.test_system}"."{self.test_name}" {self._columns_sql} VALUES %s ON CONFLICT DO NOTHING RETURNING id;'

        self.log('Created test writer with columns (%s)' % (', '.join(self.columns)))

    def _clear_memo(self):
        "Clear cache on self for memoized normalization stuff."
        # Memoization tables for each normalization
        self.branch_memo = {}
        self.machine_config_memo = {}
        self.gpu_memo = {}
        self.p4_memo = {}
        self.subtest_memo = {}
        self.test_memo = {}
        self.user_memo = {}

    def _refresh_connection(self):
        "Make sure connection is fresh if upload takes to long"
        self.connection.commit()
        self.connection.close()
        self.connection = pg_conn()

    def log(self, msg):
        print('writing result (%s:%s): %s' % (self.test_name, self.test_system, msg))

    def insert_dict(self, kwargs, dropExtra=True):
        """
        Insert a record into the test table.
        """
        return self.insert_dicts([kwargs], dropExtra)

    def get_normalized_row(self, cursor, kwargs, blob=None):
        """
        Given JSON from a client, we want to normalize the
        data before inserting it. This method uses our normalization
        routines on a known set of column names (keys in the args dictionary)
        to return a single row that can be directly inserted into the database.
        Optionally takes a blob dictionary, which will be used for the 'blob'
        column if it exists
        """
        extra = {}
        extra['blob'] = blob
        extra['gpu_id'] = normalize_gpu(cursor, self.gpu_memo, kwargs['chip_arch'], kwargs['gpu'], kwargs['gpu_ram'], kwargs['vbios']) if ('gpu_id' in self.columns) or ('machine_config_id' in self.columns) else None
        extra['p4cl_id'] = normalize_p4(cursor, self.p4_memo, kwargs['commit_id']) if 'p4cl_id' in self.columns else None
        extra['branch_id'] = normalize_branch(cursor, self.branch_memo, kwargs['branch'], kwargs['build_type']) if 'branch_id' in self.columns else None
        extra['machine_config_id'] = normalize_machine(cursor, self.machine_config_memo, kwargs['machine'], extra['gpu_id'], kwargs['cpu'], kwargs['cpu_speed'],
            kwargs['os'], kwargs['os_build'], kwargs['cpu_ram']) if 'machine_config_id' in self.columns else None
        extra['subtest_set_id'] = normalize_subtests(cursor, self.subtest_memo, kwargs['subtests']) if 'subtest_set_id' in self.columns else None
        extra['test_id'] = normalize_test(cursor, self.test_memo, kwargs['test_name']) if 'test_id' in self.columns else None
        extra['user_id'] = normalize_user(cursor, self.user_memo, kwargs['job_user']) if 'user_id' in self.columns else None
        record = []
        for col in self.columns:
            record.append(kwargs.get(col, extra.get(col, None)))
        return record
    
    def insert_dicts(self, kwargss, dropExtra=True):
        """
        Insert records into the table for the current test. Checks arguments to make
        sure all required columns are present, and prevents extra data from being entered.
        """

        # Chunk uploads so we get some progress, and don't create a huge transaction.
        for chunk_start in range(0, len(kwargss), 10):
            chunk_end = min(chunk_start + 10, len(kwargss))
            chunk = kwargss[chunk_start:chunk_end]

            self.log('building %d rows' % len(chunk))
            self._clear_memo()

            if chunk_start != 0:
                self._refresh_connection()

            with self.connection.cursor() as cursor:
                records = []
                for kwargs in chunk:

                    # Replace aliases with internal, canonical form
                    for alias, replacement in list(ALIASES.items()):
                        if alias in kwargs:
                            if replacement:
                                kwargs[replacement] = kwargs[alias]
                            del kwargs[alias]

                    # Check for extras
                    extra_columns = []
                    extra_values = []
                    for k, v in kwargs.items():
                        if k not in self.denormalized_columns:
                            extra_columns.append(k)
                            extra_values.append(v)

                    # Check for missing
                    missing_columns = []
                    for col in self.denormalized_columns:
                        if not col in kwargs:
                            if col not in self.optional_cols:
                                missing_columns.append(col)

                    # If we are missing stuff, bad!
                    if missing_columns:
                        required_columns = filter(lambda x: x not in self.optional_cols, self.denormalized_columns)
                        raise Exception('Columns [%s] not provided, expected columns [%s] - optional [%s]' % ((', ').join(missing_columns), (', ').join(required_columns), (', ').join(self.optional_cols)))

                    # Extra stuff is only sometimes bad
                    blob = None
                    if not dropExtra:
                        # If we have a 'blob' column, use that to accumulate extra fields (unless the blob field has been explicitly set)
                        if 'blob' in self.columns and 'blob' not in kwargs:
                            blob = dict(zip(extra_columns, extra_values))
                        elif extra_columns:
                            raise Exception('Extra columns [%s] provided, expected only: %s' % ((', ').join(extra_columns), (', ').join(self.denormalized_columns)))
                    records.append(self.get_normalized_row(cursor, kwargs, blob))

                self.log('adding %d rows' % len(records))

                try:
                    results = execute_values(cursor, self._insert_sql, records, fetch=True)
                    rowids = [x["id"] for x in results]
                    if rowids:
                        self.connection.commit()
                    else:
                        self.log('rolling back...')
                        self.connection.rollback()
                    return rowids
                except Exception as e:
                    self.log('rolling back...')
                    self.connection.rollback()
                    raise e

    def insert(self, **kwargs):
        """
        Similar to inset_dict, but expects it's arguments as keyword arguments.
        """
        return self.insert_dict(kwargs, False)
