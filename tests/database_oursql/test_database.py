import oursql

import pwd
import os

from testing_support.fixtures import (validate_transaction_metrics,
            validate_database_trace_inputs)

from testing_support.settings import mysql_settings

from newrelic.agent import (background_task, current_transaction,
    transient_function_wrapper)

from newrelic.common.object_wrapper import resolve_path

DB_SETTINGS = mysql_settings()

_test_execute_via_cursor_scoped_metrics = [
        ('Function/oursql:Connection', 1),
        ('Function/oursql:Connection.__enter__', 1),
        ('Function/oursql:Connection.__exit__', 1),
        ('Database/database_oursql/select', 2),
        ('Database/database_oursql/insert', 1),
        ('Database/database_oursql/update', 1),
        ('Database/database_oursql/delete', 1),
        ('Database/other/sql', 6)]

_test_execute_via_cursor_rollup_metrics = [
        ('Database/all', 12),
        ('Database/allOther', 12),
        ('Database/select', 2),
        ('Database/database_oursql/select', 2),
        ('Database/insert', 1),
        ('Database/database_oursql/insert', 1),
        ('Database/update', 1),
        ('Database/database_oursql/update', 1),
        ('Database/delete', 1),
        ('Database/database_oursql/delete', 1),
        ('Database/other', 6),
        ('Database/other/sql', 6)]

@validate_transaction_metrics('test_database:test_execute_via_cursor',
        scoped_metrics=_test_execute_via_cursor_scoped_metrics,
        rollup_metrics=_test_execute_via_cursor_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_execute_via_cursor():
    connection = oursql.connect(db=DB_SETTINGS['name'],
            user=DB_SETTINGS['user'], passwd=DB_SETTINGS['password'],
            host=DB_SETTINGS['host'], port=DB_SETTINGS['port'])

    with connection as cursor:
        cursor.execute("""drop table if exists database_oursql""")

        cursor.execute("""create table database_oursql """
                """(a integer, b real, c text)""")

        cursor.executemany("""insert into database_oursql values (?, ?, ?)""",
                [(1, 1.0, '1.0'), (2, 2.2, '2.2'), (3, 3.3, '3.3')])

        cursor.execute("""select * from database_oursql""")

        # The oursql cursor execute() method takes a non DBAPI2
        # argument to disable parameter interpolation. Also
        # changes other behaviour and actually results in a
        # speedup in execution because the default way creates a
        # prepared statement every time and then throws it away.

        cursor.execute("""select * from database_oursql""", plain_query=True)

        for row in cursor: pass

        cursor.execute("""update database_oursql set a=?, b=?, c=? """
                """where a=?""", (4, 4.0, '4.0', 1))

        cursor.execute("""delete from database_oursql where a=2""")

    connection.commit()
    connection.rollback()
    connection.commit()

_test_rollback_on_exception_scoped_metrics = [
        ('Function/oursql:Connection', 1),
        ('Function/oursql:Connection.__enter__', 1),
        ('Function/oursql:Connection.__exit__', 1),
        ('Database/other/sql', 1)]

_test_rollback_on_exception_rollup_metrics = [
        ('Database/all', 2),
        ('Database/allOther', 2),
        ('Database/other', 1),
        ('Database/other/sql', 1)]

@validate_transaction_metrics('test_database:test_rollback_on_exception',
        scoped_metrics=_test_rollback_on_exception_scoped_metrics,
        rollup_metrics=_test_rollback_on_exception_rollup_metrics,
        background_task=True)
@validate_database_trace_inputs(sql_parameters_type=tuple)
@background_task()
def test_rollback_on_exception():
    try:
        connection = oursql.connect(db=DB_SETTINGS['name'],
                user=DB_SETTINGS['user'], passwd=DB_SETTINGS['password'],
                host=DB_SETTINGS['host'], port=DB_SETTINGS['port'])

        with connection as cursor:
            raise RuntimeError('error')
    except RuntimeError:
        pass