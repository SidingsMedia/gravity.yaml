# SPDX-FileCopyrightText: 2023 Sidings Media
# SPDX-License-Identifier: MIT

class DatabaseError(Exception):
    """An error occurred with the database"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ConfigFileError(Exception):
    """An error occurred with the config file"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
