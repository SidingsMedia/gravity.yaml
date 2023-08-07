# SPDX-FileCopyrightText: 2023 Sidings Media
# SPDX-License-Identifier: MIT

from datetime import datetime
import pathlib
import os
import sqlite3

import yaml

import gravityyaml.errors as errors
from gravityyaml.database import Database

class GravityYAML:
    def __init__(self, yaml_path: str, db_path: str) -> None:
        """
        :param yaml_path: Path to YAML config file
        :type yaml_path: str
        :param db_path: Directory to store database in
        :type db_path: str
        """

        self._database = None
        self._data = None
        self._db_path = os.path.join(db_path, "gravity.db")
        self._yaml_path = yaml_path

    def init_database(self) -> None:
        """
        init_database Create the gravity.db database

        Create a new, empty gravity.db database at the given path. If
        the database already exists, it will be moved to
        gravity.db.old-{date} before the new database is created.
        """

        if os.path.isfile(self._db_path):
            now = datetime.today().strftime('%Y-%m-%d')
            os.rename(self._db_path, self._db_path + ".old-" + now)

        pathlib.Path(self._db_path).touch()

    def load_yaml(self) -> None:
        """
        load_yaml Load YAML file from disk

        Load the YAML configuration file ready for parsing.
        """

        if not os.path.isfile(self._yaml_path):
            raise FileNotFoundError(message="YAML config file could not be found.")

        with open(self._yaml_path, "r") as f:
            self._data = yaml.safe_load(f)

        if len(self._data["adlists"]) < 1:
            raise errors.ConfigFileError("No ad lists specified")

    def populate_database(self) -> None:
        """
        populate_database Populate database tables

        Populates the database tables using the loaded data
        """

        if not self._data:
            raise errors.ConfigFileError("Config file not loaded. Did you forget to call load_yaml?")
        
        script_path = os.path.dirname(os.path.realpath(__file__))
        if not os.path.isfile(os.path.join(script_path, "database.sql")):
            raise FileNotFoundError("Could not find database schema")

        with Database(self._db_path) as conn:
            conn.loadFile(os.path.join(script_path, "database.sql"))
            group_index = {"Default": 0}

            for group in self._data["groups"]:
                group_index[group["name"]] = conn.insert(
                    table="group",
                    columns=("enabled", "name", "description"),
                    values=(
                        group.get("enabled", True),
                        group["name"],
                        group.get("description", None),
                    )
                )

            for adlist in self._data["adlists"]:
                list_id = conn.insert(
                    table="adlist",
                    columns=("address", "enabled", "comment"),
                    values=(
                        adlist["url"],
                        adlist.get("enabled", True),
                        adlist.get("description", None),
                    )
                )

                for group in adlist["groups"]:
                    try:
                        group_id = group_index[group]
                    except KeyError:
                        print(f"WARNING - Group {group} referenced by adlist {adlist['url']} does not exist")
                        continue

                    if group_id == 0:
                        # Relationship automatically added for Default
                        continue

                    conn.insert(
                        table="adlist_by_group",
                        columns=("adlist_id", "group_id"),
                        values=(list_id, group_id)
                    )

            conn.commit()

    def run(self) -> None:
        """
        run Setup a new gravity database ready for use

        Read the YAML config file and then setup a new gravity DB to
        match
        """

        self.load_yaml()
        self.init_database()
        self.populate_database()
