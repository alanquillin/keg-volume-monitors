# pylint: disable=wrong-import-position
_TABLE_NAME = "device_measurements"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, String, func, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import Base, DictifiableMixin, QueryMethodsMixin
from db.types.nested import NestedMutableDict


class DeviceMeasurements(Base, DictifiableMixin, QueryMethodsMixin):
    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    device_id = Column(UUID, ForeignKey("devices.id"), nullable=False)
    measurement = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    taken_on = Column(DateTime(timezone=True), nullable=False)

    device = relationship("Devices", back_populates="measurements")

    __table_args__ = (
        Index("ix_device_measurements_by_device_id", device_id, unique=False),
        Index("ix_ordered_device_measurements_by_device_id_and_measure", device_id, measurement, taken_on.desc(), unique=False),
    )
    
    @classmethod
    def get_by_device_id(cls, session, device_id, **kwargs):
        return session.query(cls).filter_by(device_id=device_id, **kwargs)
    
    @classmethod
    def get_latest_measurement(cls, session, device_id, **kwargs):
        return session.query(cls).filter_by(device_id=device_id, **kwargs).order_by(DeviceMeasurements.taken_on.desc()).first()