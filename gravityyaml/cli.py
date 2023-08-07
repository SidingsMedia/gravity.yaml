# SPDX-FileCopyrightText: 2023 Sidings Media
# SPDX-License-Identifier: MIT

import argparse
import sys

from gravityyaml.gravityyaml import GravityYAML
import gravityyaml.errors as errors

EXIT_CODES = {
    "DEFAULT": 1,
    "DATABASE_ERROR": 2,
    "CONFIG_FILE_ERROR": 3,
    "FILE_ERROR": 4,
}

def cli() -> None:
    """Start the CLI"""

    parser = argparse.ArgumentParser(
        prog="gravityyaml",
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
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    app = GravityYAML(args.config, args.database)
    if args.debug:
        app.run()
    else:
        try:
            app.run()
        except errors.DatabaseError as e:
            print(f"FATAL - {e}")
            sys.exit(EXIT_CODES["DATABASE_ERROR"])
        except Exception as e:
            print(f"FATAL - {e}")
            sys.exit(EXIT_CODES["DEFAULT"])
