# coding=UTF-8

import pytest
import pymysql
from textwrap import dedent
from utils import run, dbtest, set_expanded_output

@dbtest
def test_conn(executor):
    run(executor, '''create table test(a text)''')
    run(executor, '''insert into test values('abc')''')
    results = run(executor, '''select * from test''', join=True)
    assert results == dedent("""\
        +-----+
        | a   |
        |-----|
        | abc |
        +-----+
        1 row in set""")

@dbtest
def test_bools(executor):
    run(executor, '''create table test(a boolean)''')
    run(executor, '''insert into test values(True)''')
    results = run(executor, '''select * from test''', join=True)
    assert results == dedent("""\
        +-----+
        |   a |
        |-----|
        |   1 |
        +-----+
        1 row in set""")

@dbtest
def test_table_and_columns_query(executor):
    run(executor, "create table a(x text, y text)")
    run(executor, "create table b(z text)")

    assert set(executor.tables()) == set([('a',), ('b',)])
    assert set(executor.table_columns()) == set(
            [('a', 'x'), ('a', 'y'), ('b', 'z')])

@dbtest
def test_database_list(executor):
    databases = executor.databases()
    assert '_test_db' in databases

@dbtest
def test_invalid_syntax(executor):
    with pytest.raises(pymysql.ProgrammingError) as excinfo:
        run(executor, 'invalid syntax!')
    assert 'You have an error in your SQL syntax;' in str(excinfo.value)

@dbtest
def test_invalid_column_name(executor):
    with pytest.raises(pymysql.InternalError) as excinfo:
        run(executor, 'select invalid command')
    assert "Unknown column 'invalid' in 'field list'" in str(excinfo.value)

@dbtest
def test_unicode_support_in_output(executor):
    run(executor, "create table unicodechars(t text)")
    run(executor, "insert into unicodechars (t) values ('é')")

    # See issue #24, this raises an exception without proper handling
    assert u'é' in run(executor, "select * from unicodechars", join=True)

@dbtest
def test_expanded_output(executor):
    run(executor, '''create table test(a text)''')
    run(executor, '''insert into test values('abc')''')
    results = run(executor, '''select * from test\G''', join=True)

    expected_results = set([
        dedent("""\
        -[ RECORD 0 ]
        a | abc

        1 row in set"""),
        dedent("""\
        ***************************[ 1. row ]***************************
        a | abc

        1 row in set"""),
    ])

    assert results in expected_results

@dbtest
def test_multiple_queries_same_line(executor):
    result = run(executor, "select 'foo'; select 'bar'")
    assert len(result) == 4  # 2 for the results and 2 more for status messages.
    assert "foo" in result[0]
    assert "bar" in result[2]

@dbtest
def test_multiple_queries_same_line_syntaxerror(executor):
    with pytest.raises(pymysql.ProgrammingError) as excinfo:
        run(executor, "select 'foo'; invalid syntax")
    assert 'You have an error in your SQL syntax;' in str(excinfo.value)

@dbtest
def test_favorite_query(executor):
    set_expanded_output(False)
    run(executor, "create table test(a text)")
    run(executor, "insert into test values('abc')")
    run(executor, "insert into test values('def')")

    results = run(executor, "\\fs test-a select * from test where a like 'a%'")
    assert results == ['Saved.']

    results = run(executor, "\\f test-a", join=True)
    assert results == dedent("""\
           > select * from test where a like 'a%'
           +-----+
           | a   |
           |-----|
           | abc |
           +-----+""")

    results = run(executor, "\\fd test-a")
    assert results == ['test-a: Deleted']

@dbtest
def test_favorite_query_multiple_statement(executor):
    set_expanded_output(False)
    run(executor, "create table test(a text)")
    run(executor, "insert into test values('abc')")
    run(executor, "insert into test values('def')")

    results = run(executor, "\\fs test-ad select * from test where a like 'a%'; "
                            "select * from test where a like 'd%'")
    assert results == ['Saved.']

    results = run(executor, "\\f test-ad", join=True)
    assert results == dedent("""\
           > select * from test where a like 'a%'
           +-----+
           | a   |
           |-----|
           | abc |
           +-----+
           > select * from test where a like 'd%'
           +-----+
           | a   |
           |-----|
           | def |
           +-----+""")

    results = run(executor, "\\fd test-ad")
    assert results == ['test-ad: Deleted']

@dbtest
def test_special_command(executor):
    results = run(executor, '\\?')
    expected_line = u'| help      | \\?             | Show this help.                              |\n'
    assert len(results) == 1
    assert expected_line in results[0]

@dbtest
def test_unicode_support(executor):
    assert u'日本語' in run(executor, "SELECT '日本語' AS japanese;", join=True)

@dbtest
def test_favorite_query_multiline_statement(executor):
    set_expanded_output(False)
    run(executor, "create table test(a text)")
    run(executor, "insert into test values('abc')")
    run(executor, "insert into test values('def')")

    results = run(executor, "\\fs test-ad select * from test where a like 'a%';\n"
                            "select * from test where a like 'd%'")
    assert results == ['Saved.']

    results = run(executor, "\\f test-ad", join=True)
    assert results == dedent("""\
           > select * from test where a like 'a%'
           +-----+
           | a   |
           |-----|
           | abc |
           +-----+
           > select * from test where a like 'd%'
           +-----+
           | a   |
           |-----|
           | def |
           +-----+""")

    results = run(executor, "\\fd test-ad")
    assert results == ['test-ad: Deleted']
