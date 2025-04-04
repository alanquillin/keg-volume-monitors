#!/usr/bin/env python3

import argparse
from datetime import datetime
import logging
import os
import sys
from time import sleep

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.sql import text

#from db import Base

def seed_db(db_session, db, items, pk="id"):
    for item in items:
        logger.info(item)
        try:
            if not db.get_by_pkey(db_session, item.get(pk)):
                logger.info("Seeding %s: %s", db.__name__, item)
                db.create(db_session, **item)
            else:
                logger.info("Item %s already exists in %s.", item[pk], db.__name__)
        except IntegrityError as ex:
                logger.debug("Item already exists or a constraint was violated: %s", ex)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # parse logging level arg:
    parser.add_argument(
        "-l",
        "--log",
        dest="loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO").upper(),
        help="Set the logging level",
    )

    args = parser.parse_args()
    log_level = getattr(logging, args.loglevel)
    logging.basicConfig(level=log_level, format="%(levelname)-8s: %(asctime)-15s [%(name)s]: %(message)s")
    logger = logging.getLogger()

    config = Config()
    config.setup(config_files=["default.json"])

    skip_db_seed = config.get("db.seed.skip")
    if skip_db_seed:
        logger.info("Skipping DB Seeding")
        sys.exit()

    logger.debug("config: %s", config.data_flat)
    logger.debug("db host: %s", config.get("db.host"))
    logger.debug("db username: %s", config.get("db.username"))
    logger.debug("db port: %s", config.get("db.port"))
    logger.debug("db name: %s", config.get("db.name"))
    logger.debug("db password: %s", config.get("db.password"))


    with session_scope(config) as db_session:
        while True:
            try:
                db_session.execute(text("select 1"))
                logger.debug("Database ready!")
                break
            except OperationalError:
                logger.debug("Waiting for database readiness")
                sleep(3)

        logger.debug("Creating database schema and seeding with data")
