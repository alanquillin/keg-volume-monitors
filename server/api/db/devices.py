# pylint: disable=wrong-import-position
_TABLE_NAME = "devices"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, String, func, and_
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from db import Base, DictifiableMixin, QueryMethodsMixin
from db.types.nested import NestedMutableDict


class Devices(Base, DictifiableMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    manufacturer_id = Column(String, nullable=False)
    meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)

    measurements = relationship("DeviceMeasurements", back_populates="device")

    __table_args__ = (Index("ix_sensor_manufacturer_and_manufacturer_id", manufacturer, manufacturer_id, unique=False),)

    @classmethod
    def get_by_manufacturer_id(cls, session, manufacturer, manufacturer_id, **kwargs):
        return session.query(cls).filter(and_(Devices.manufacturer.ilike(manufacturer), Devices.manufacturer_id.ilike(manufacturer_id)))
