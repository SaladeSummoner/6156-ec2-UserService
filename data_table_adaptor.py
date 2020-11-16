import pymysql
import dbutils
import RDBDatatable

# The REST application server app.py will be handling multiple requests over a long period of time.
# It is inefficient to create an instance of RDBDataTable for each request.  This is a cache of created
# instances.
_db_tables = {}

def get_rdb_table(table_name, db_name, key_columns=None, connect_info=""):
    """

    :param table_name: Name of the database table.
    :param db_name: Schema/database name.
    :param key_columns: This is a trap. Just use None.
    :param connect_info: You can specify if you have some special connection, but it is
        OK to just use the default connection.
    :return:
    """

    global _db_tables

    # We use the fully qualified table name as the key into the cache, e.g. lahman2019clean.people.
    key = db_name + "." + table_name

    # Have we already created and cache the data table?
    result = _db_tables.get(key, None)

    # We have not yet accessed this table.
    if result is None:

        # Make an RDBDataTable for this database table.
        result = RDBDatatable.RDBDataTable(table_name, db_name, key_columns, connect_info)

        # Add to the cache.
        _db_tables[key] = result

    return result


def get_databases():
    """

    :return: A list of databases/schema at this endpoint.
    """

    # -- TO IMPLEMENT --
    q = "show databases"
    res, d = dbutils.run_q(q, conn=_conn)
    return d


def get_tables(dbname):

    q="select table_name from information_schema.tables where table_schema = '" + dbname + "'"
    # print(q,"This is q in get_table")
    res, d = dbutils.run_q(q, conn=_conn)
    # print(d)
    return d









