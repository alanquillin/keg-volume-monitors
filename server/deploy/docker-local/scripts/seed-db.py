#!/usr/bin/env python3

import argparse
from datetime import datetime, timezone
import logging
import os
import sys
from time import sleep

from db import Base, session_scope, devices, device_measurements
from lib.config import Config

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.sql import text

#from db import Base

DEVICE_ID_1 = "022041b5-89af-45ee-87ef-135f68c25f3f"
DEVICE_ID_2 = "13353ea9-bf7f-41d3-bd82-97262bf6a97a"
DEVICES = [
    {
        "id": DEVICE_ID_1,
        "name": "Photon - 1",
        "chip_type": "particle",
        "chip_id": "31003c001747343337363432",
        "chip_model": "Photon",
        "device_type": "weight",
        "empty_keg_weight": 4400,
        "empty_keg_weight_unit": "g",
        "start_volume": 18927.059, # 5 gallons
        "start_volume_unit": "ml",
        "display_volume_unit": "ml"
    },
    {
        "id": DEVICE_ID_2,
        "name": "Photon2 - 1",
        "chip_type": "particle",
        "chip_model": "Photon2",
        "chip_id": "0a10aced202194944a054e68",
        "device_type": "weight",
        "empty_keg_weight": 4400,
        "empty_keg_weight_unit": "g",
        "start_volume": 18927.059, # 5 gallons
        "start_volume_unit": "ml",
        "display_volume_unit": "ml"
    }
]

MEASUREMENT_ID_1 = "d4dafc76-94c2-40fd-af8a-93fdacc74dff"
MEASUREMENT_ID_2 = "c5cac4e9-495a-4a33-b781-0f43cc34482d"
MEASUREMENT_ID_3 = "9348ac29-af33-404f-affd-e60a3da92d8a"
MEASUREMENT_ID_4 = "9a01c621-edb9-4524-9309-6e3ce8db90cf"
MEASUREMENT_ID_5 = "46996c5b-e7ba-444d-a23a-fffe8dd07f59"
MEASUREMENT_ID_6 = "f4117dd9-0a54-4a40-ae24-4593eb22a704"
MEASUREMENT_ID_7 = "b1d00235-54d7-45f0-9d08-2ac45ce6e5db"
MEASUREMENT_ID_8 = "84e31930-3461-41b0-a89a-8169a1e13b20"
MEASUREMENT_ID_9 = "081e19b4-73ff-4a4c-9a45-fdf3fc512da7"
MEASUREMENT_ID_10 = "4da763d8-65df-4f78-a59f-bb855b4992ce"
MEASUREMENT_ID_11 = "917f1581-0d66-4e9e-924a-37a54c9126f1"
MEASUREMENT_ID_12 = "090c35e1-01c7-4099-8b6e-478280d41f98"
MEASUREMENT_ID_13 = "78b30327-13de-4790-9bd4-c403266e4ff1"
MEASUREMENTS = [
    {
        "id": MEASUREMENT_ID_1,
        "device_id": DEVICE_ID_1,
        "measurement": 23220.0,
        "unit": "g",
        "taken_on": datetime(2025, 4, 3, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_2,
        "device_id": DEVICE_ID_1,
        "measurement": 22155.354,
        "unit": "g",
        "taken_on": datetime(2025, 4, 4, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_3,
        "device_id": DEVICE_ID_1,
        "measurement": 21445.59,
        "unit": "g",
        "taken_on": datetime(2025, 4, 5, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_4,
        "device_id": DEVICE_ID_1,
        "measurement": 17541.88,
        "unit": "g",
        "taken_on": datetime(2025, 4, 6, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_5,
        "device_id": DEVICE_ID_1,
        "measurement": 15767.478,
        "unit": "g",
        "taken_on": datetime(2025, 4, 7, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_6,
        "device_id": DEVICE_ID_1,
        "measurement": 9024.72,
        "unit": "g",
        "taken_on": datetime(2025, 4, 8, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_7,
        "device_id": DEVICE_ID_1,
        "measurement": 8314.956,
        "unit": "g",
        "taken_on": datetime(2025, 4, 9, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_8,
        "device_id": DEVICE_ID_1,
        "measurement": 6895.428,
        "unit": "g",
        "taken_on": datetime(2025, 4, 10, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_9,
        "device_id": DEVICE_ID_2,
        "measurement": 6185.664,
        "unit": "g",
        "taken_on": datetime(2025, 4, 3, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_10,
        "device_id": DEVICE_ID_2,
        "measurement": 5109.764,
        "unit": "g",
        "taken_on": datetime(2025, 4, 3, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_11,
        "device_id": DEVICE_ID_2,
        "measurement": 4432.0,
        "unit": "g",
        "taken_on": datetime(2025, 4, 3, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_12,
        "device_id": DEVICE_ID_2,
        "measurement": 62678.8,
        "unit": "g",
        "taken_on": datetime(2025, 4, 3, 6, 32, 00, tzinfo=timezone.utc)
    },
    {
        "id": MEASUREMENT_ID_13,
        "device_id": DEVICE_ID_2,
        "measurement": 5200,
        "unit": "g",
        "taken_on": datetime(2025, 4, 3, 6, 32, 00, tzinfo=timezone.utc)
    }
]

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

        seed_db(db_session, devices.Devices, DEVICES)
        seed_db(db_session, device_measurements.DeviceMeasurements, MEASUREMENTS)
