#!/usr/bin/env python3
"""
Contains connection objects and helper functions to connect and run SQL on Oracle databases
"""
import cx_Oracle
import sqlparse
from .__init__ import *
from .custom_exception import CommonException


class DatabaseConnectionFailed(CommonException):
    pass


class OracleDatabase(object):

    def __init__(self, db_hostname='db', db_user='SYS', db_passwd='Welcome1!', service_name='MYPDB', db_user_role='SYSDBA', log_domain=''):
        self.db_hostname = db_hostname
        self.db_passwd = db_passwd
        self.db_user = db_user
        self.db_user_role = db_user_role
        self.service_name = service_name
        self.log_domain = log_domain

        self.log = logging.getLogger(self.log_domain)

        # Global DB connection object
        self.connection_object = None

        # Global DB cursor object
        self.cursor = None

    def run_sql_script(self, sql_file_path):
        """
        Execute all SQL statements in a given file

        :param sql_file_path:   The path of the SQL file to run
        :type sql_file_path:    str
        :return:                None
        :rtype:                 None
        """
        with open(sql_file_path, 'r') as sql_file:
            for sql_query in sqlparse.split(sql_file.read()):
                if sql_query:
                    self.log.debug(f'Executing SQL:\n{sql_query}')
                    self.run_sql(sql_query)

    def run_sql(self, sql_query):
        """Execute arbitrary SQL against the database.

        Run a given SQL query against the database. Must provide a connection object which can be obtained
        by calling the `wait_for_db()` function first.

        :param sql_query:   SQL query to execute against the DB
        :type sql_query:    str
        :return:            0 for success, 1 for failure
        """
        try:
            # Remove any semicolons from the end of SQL statements to avoid a parsing error from Oracle
            sql_query = sql_query.replace(';', '')

            self.cursor.execute(sql_query)
        except cx_Oracle.DatabaseError as dbe:
            self.log.exception(dbe)

    def close(self):
        """Close the DB connection.

        Closes the connection to the database.

        :return:    None
        :rtype:     None
        """
        if self.connection_object:
            self.connection_object.close()

    def connect(self, max_attempts=15, sleep_time=30):
        """Create a database connection.

        Waits for the database to become available by attempting to connect. The connection will be retried by the
        number of times defined by `max_attempts` and will wait for `sleep_time` seconds between each attempt. If
        the number of connection attempts is exhausted then an exception is raised.

        :raises                 DatabaseConnectionFailed
        :param max_attempts     The maximum number of times the connection will be attempted before failing
        :type max_attempts      int
        :param sleep_time       The wait time between attempts, in seconds
        :type sleep_time        int
        :return:                True if connection is successful
        :rtype:                 bool
        """
        n = 0

        connection_params = {
            'user': self.db_user,
            'password': self.db_passwd,
            'dsn': f'{self.db_hostname}/{self.service_name}'
        }

        if self.db_user_role:
            connection_params['mode'] = getattr(cx_Oracle, self.db_user_role.upper())

        self.log.info(f'Using connection parameters: {connection_params}')
        self.log.info('Attempting database connection...')

        while n < max_attempts:
            n += 1

            self.log.info(f'Connection attempt {n}/{max_attempts}')

            try:
                self.connection_object = cx_Oracle.connect(**connection_params)
                self.log.info('Successfully connected to the database!')

                if not self.cursor:
                    self.cursor = self.connection_object.cursor()

                return True
            except cx_Oracle.DatabaseError as dbe:
                self.log.warning(f'Connection attempt failed; error: {dbe}')
                if n < max_attempts:
                    self.log.info(f'Database not ready; sleeping for {sleep_time} seconds...')
                    time.sleep(sleep_time)
                else:
                    raise DatabaseConnectionFailed('Unable to establish a connection to the database.')
