# SPDX-FileCopyrightText: 2023 Sidings Media
# SPDX-License-Identifier: MIT

import argparse
from datetime import datetime
import os
import sqlite3
import sys

import yaml

class Application:
    def __init__(self, yaml_path: str, db_path: str) -> None:
        """
        :param yaml_path: Path to YAML config file
        :type yaml_path: str
        :param db_path: Directory to store database in
        :type db_path: str
        """

        self._connection = None
        self._cursor = None
        self._data = None
        self._db_path = os.path.join(db_path, "gravity.db")
        self._yaml_path = yaml_path

    def _init_database(self) -> None:
        """
        _init_database Create the gravity.db database

        Create a new, empty gravity.db database at the given path. If
        the database already exists, it will be moved to
        gravity.db.old-{date} before the new database is created.
        """

        if os.path.isfile(self._db_path):
            now = datetime.today().strftime('%Y-%m-%d')
            os.rename(self._db_path, self._db_path + ".old-" + now)

        script_path = os.path.dirname(os.path.realpath(__file__))
        if not os.path.isfile(os.path.join(script_path, "database.sql")):
            print("ERROR - Could not find database schema")
            sys.exit(1)
        
        with open(os.path.join(script_path, "database.sql"), "r") as f:
            sql = f.read()

        self._connection = sqlite3.connect(self._db_path)
        self._connection.executescript(sql)

    def _load_yaml(self) -> None:
        """
        _load_yaml Load YAML file from disk

        Load the YAML configuration file ready for parsing.
        """

        if not os.path.isfile(self._yaml_path):
            print("ERROR - Could not find YAML file")
            sys.exit(1)

        with open(self._yaml_path, "r") as f:
            self._data = yaml.safe_load(f)

        if len(self._data["adlists"]) < 1:
            print("ERROR - No ad lists specified")
            sys.exit(1)

    def _populate_database(self) -> None:
        """
        _populate_database Populate database tables

        Populates the database tables using the loaded data
        """

        if not self._data:
            print("ERROR - Config file not loaded")
            sys.exit(1)

        if not self._connection:
            print("ERROR - Database has not been initialized")
            sys.exit(1)
        
        self._cursor = self._connection.cursor()
        group_index = {"Default": 0}

        for group in self._data["groups"]:
            self._cursor.execute(
                "INSERT INTO 'group' (enabled, name, description) VALUES (?,?,?);",
                (
                    group.get("enabled", True),
                    group["name"],
                    group.get("description", None),
                )
            )
            group_index[group["name"]] = self._cursor.lastrowid

        for adlist in self._data["adlists"]:
            self._cursor.execute(
                "INSERT INTO adlist (address, enabled, comment) VALUES (?,?,?);",
                (
                    adlist["url"],
                    adlist.get("enabled", True),
                    adlist.get("description", None),
                )
            )
            list_id = self._cursor.lastrowid

            for group in adlist["groups"]:
                try:
                    group_id = group_index[group]
                except KeyError:
                    print(f"WARNING - Group {group} referenced by adlist {adlist['url']} does not exist")
                    continue

                if group_id == 0:
                    # Relationship automatically added for Default
                    continue
                
                self._cursor.execute(
                    "INSERT INTO adlist_by_group(adlist_id, group_id) VALUES (?,?);",
                    (list_id, group_id)
                )

        self._connection.commit()

    def run(self) -> None:
        """Start application"""

        self._load_yaml()
        self._init_database()
        try:
            self._populate_database()
        finally:
            if self._cursor:
                self._cursor.close()
                self._cursor = None
            self._connection.close()
            self._connection = None


def main() -> None:
    """Application entry point"""

    parser = argparse.ArgumentParser(
        description="Store Pi-hole gravity.db config in a YAML file"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str, 
        default="gravity.yaml",
        metavar="PATH",
        help="Path to gravity.yaml config file. Defaults to gravity.yaml.",
    )
    parser.add_argument(
        "-d", 
        "--database",
        type=str, 
        default="/etc/pihole/",
        metavar="PATH",
        help="Path to database directory. Defaults to /etc/pihole/.",
    )
    args = parser.parse_args()

    app = Application(args.config, args.database)
    app.run()

if __name__ == "__main__":
    main()
