# pylint: disable=wrong-import-position
_TABLE_NAME = "devices"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, String, func, and_
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from db import Base, DictifiableMixin, QueryMethodsMixin, try_return_all
from db.types.nested import NestedMutableDict


class Devices(Base, DictifiableMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    chip_type = Column(String, nullable=False)
    chip_id = Column(String, nullable=False)
    chip_model = Column(String, nullable=True)
    meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)

    measurements = relationship("DeviceMeasurements", back_populates="device")

    __table_args__ = (Index("ix_sensor_chip_type_and_chip_id", chip_type, chip_id, unique=False),)

    @classmethod
    def get_by_chip_id(cls, session, chip_type, chip_id, **kwargs):
        return try_return_all(session.query(cls).filter(and_(Devices.chip_type.ilike(chip_type), Devices.chip_id.ilike(chip_id))))

