# pylint: disable=wrong-import-position
_TABLE_NAME = "devices"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, String, func, and_, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.schema import Index

from db import Base, DictifiableMixin, QueryMethodsMixin, try_return_all
from db.device_measurements import DeviceMeasurements
from db.types.nested import NestedMutableDict


class Devices(Base, DictifiableMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)
    chip_type = Column(String, nullable=False)
    chip_id = Column(String, nullable=False)
    chip_model = Column(String, nullable=True)
    empty_keg_weight = Column(Float, nullable=True)
    empty_keg_weight_unit = Column(String, nullable=True)
    start_volume = Column(Float, nullable = False)
    start_volume_unit = Column(String, nullable=False)
    display_volume_unit = Column(String, nullable=False)
    meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)

    _measurement_count = None
    @hybrid_property
    def measurement_count(self):
        return self._measurement_count
    @measurement_count.setter
    def measurement_count(self, value):
        self._measurement_count = value

    _latest_measurement = None
    @hybrid_property
    def latest_measurement(self):
        return self._latest_measurement
    @latest_measurement.setter
    def latest_measurement(self, value):
        self._latest_measurement = value

    _latest_measurement_unit = None
    @hybrid_property
    def latest_measurement_unit(self):
        return self._latest_measurement_unit
    @latest_measurement_unit.setter
    def latest_measurement_unit(self, value):
        self._latest_measurement_unit = value
    
    _latest_measurement_taken_on = None
    @hybrid_property
    def latest_measurement_taken_on(self):
        return self._latest_measurement_taken_on
    @latest_measurement_taken_on.setter
    def latest_measurement_taken_on(self, value):
        self._latest_measurement_taken_on = value

    measurements = relationship("DeviceMeasurements", back_populates="device")

    __table_args__ = (Index("ix_sensor_chip_type_and_chip_id", chip_type, chip_id, unique=False),)

    @classmethod
    def _get_with_measurement_stats(cls, session, filters=None, **kwargs):
        query = session.query(cls, func.count(DeviceMeasurements.id).label("measurement_count"))
        if filters:
            query = query.filter(*filters)
        return query.join(DeviceMeasurements).group_by(Devices.id)

    @classmethod
    def _parse_response_with_measurement_stats(cls, session, res):
        dev = None
        if type(res) is Devices:
            dev = res
        else:
            dev = res[0]
            dev.measurement_count = res[1]

        latest_measurement = DeviceMeasurements.get_latest_measurement(session, dev.id)
        dev.latest_measurement = latest_measurement.measurement
        dev.latest_measurement_unit = latest_measurement.unit
        dev.latest_measurement_taken_on = latest_measurement.taken_on

        return dev
    
    @classmethod
    def _all_with_measurement_stats(cls, session, filters=None, **kwargs):
        res = try_return_all(Devices._get_with_measurement_stats(session, filters))
        if not res:
            return res
        
        devices = []
        for r in res:
            devices.append(Devices._parse_response_with_measurement_stats(session, r))

        return devices
    
    @classmethod
    def get_with_measurement_stats(cls, session, pk_id,**kwargs):
        res = Devices._get_with_measurement_stats(session, (Devices.id == pk_id)).first()
        return Devices._parse_response_with_measurement_stats(session, res)
        
    @classmethod
    def get_all_with_measurement_stats(cls, session, **kwargs):
        return Devices._all_with_measurement_stats(session)
                 
    @classmethod
    def get_by_chip_id(cls, session, chip_type, chip_id, **kwargs):
        return Devices._all_with_measurement_stats(session, (and_(Devices.chip_type.ilike(chip_type), Devices.chip_id.ilike(chip_id))))
    

        

