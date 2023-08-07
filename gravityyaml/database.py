# SPDX-FileCopyrightText: 2023 Sidings Media
# SPDX-License-Identifier: MIT

from __future__ import annotations
import sqlite3

class Database:
    """Handle management of the sqlite3 database"""

    def __init__(self, db_path: str) -> None:
        """
        __init__ Constructor method

        :param db_path: Path to database
        :type db_path: str
        :raises FileExistsError: The database file already exists
        """
        
        self._db_path = db_path
        self._connection = None
        self._cursor = None

    def __enter__(self) -> Database:
        """
        __enter__ Enter with statement

        :return: This instance of Database
        :rtype: Database
        """

        self._connection = sqlite3.connect(self._db_path)
        self._cursor = self._connection.cursor()
        return self

    def __exit__(self, exception_type: str, exception_value: str, traceback: str) -> bool:
        """
        __exit__ Handle exit of with

        :param exception_type: Type of exception raised
        :type exception_type: str
        :param exception_value: Value of exception raised
        :type exception_value: str
        :param traceback: Traceback for exception
        :type traceback: str
        :return: Has the exception been suppressed?
        :rtype: bool
        """

        self._cursor.close()
        self._connection.close()
        return False
    
    @staticmethod
    def sanitise_string(string: str) -> str:
        return ''.join( chr for chr in string if chr.isalnum() or chr == "_" )

    def loadFile(self, path: str) -> None:
        """
        loadFile Load an SQL file from disk and execute it

        Loads the specified SQL file and then executes it in full. No
        validation or sanitisation of the SQL file is done, therefore it
        is not recommended to run files from untrusted sources, such as
        those that have been received over a network unless prior
        verification of their contents has been completed.

        :param path: Path to SQL file
        :type path: str
        """

        with open(path, "r") as f:
            sql = f.read()
            self._cursor.executescript(sql)
    
    def insert(self, table: str, columns: tuple[str], values: tuple[str]) -> int:
        """
        insert Insert a row into the database

        Insert the provided values into the specified table in the
        database and return the ID of the newly inserted row.

        :param table: Name of table to insert
        :type table: str
        :param columns: List of columns to insert
        :type columns: tuple[str]
        :param values: List of values to insert. Order must match that
            of the columns.
        :type values: tuple[str]
        :return: ID of row
        :rtype: int
        :raises ValueError: The length of the columns list does not
            match the length of the values list 
        :raises ValueError: Table name contains invalid characters
        """

        if len(columns) != len(values):
            raise ValueError("Length of columns does not match length of values")
        
        sanitised_table = Database.sanitise_string(table)
        if sanitised_table != table:
            raise ValueError("Table name contained invalid characters. Allowed characters are a-z,A-Z,0-9 and _.")
        
        sanitised_columns = []
        for column in columns:
            sanitised_column = Database.sanitise_string(column)
            if sanitised_column != column:
                raise ValueError("Column name contained invalid characters. Allowed characters are a-z,A-Z,0-9 and _.")
            sanitised_columns.append("'" + sanitised_column + "'")
        
        column_placeholders = ",".join(sanitised_columns)
        value_placeholders = ",".join("?" * len(values))
        template = f"INSERT INTO '{sanitised_table}' ({column_placeholders}) VALUES ({value_placeholders});"

        self._cursor.execute(template, values)
        return self._cursor.lastrowid

    def commit(self) -> None:
        """Commit changes to database"""

        self._connection.commit()
        