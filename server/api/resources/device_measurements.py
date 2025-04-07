from datetime import datetime

from db import session_scope
from db.devices import Devices as DevicesDB
from db.device_measurements import DeviceMeasurements as DeviceMeasurementsDB
from lib.time import utcnow_aware
from resources import BaseResource

from flask_restx import Namespace, Resource, fields

api = Namespace('device_measurements', description='Manage Device Measurements')

IN_FIELDS = {
    'device_id': fields.String(required=True, description="The device Id"),
    'measurement': fields.Float(required=True, description='The value of the taken measurement'),
    'unit': fields.String(required=False, description='The unit of the taken measurement'),
    "taken_on": fields.DateTime(requires=False, description="The datetime that the measurement was taken.")
}

save_device_measurement_mod = api.model('SaveDeviceMeasurement', IN_FIELDS)
device_measurement_mod = api.model('DeviceMeasurement', {
        'id': fields.String(required=True, description='The id of the device', readonly=True)
    } | IN_FIELDS)

@api.route('/')
class DeviceMeasurements(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('list_device_measurements')
    @api.marshal_list_with(device_measurement_mod)
    def get(self, device_id):
        data = []
        with session_scope(self.config) as db_session:
            measurements = DeviceMeasurementsDB.query(db_session, device_id=device_id)
            if measurements:
                for m in measurements:
                    data.append(m.to_dict())
        return data
    
    @api.doc('save_device_measurement')
    @api.expect(save_device_measurement_mod, validate=True)
    @api.marshal_list_with(device_measurement_mod, code=201)
    def post(self, device_id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, device_id)
            if not dev:
                api.abort(404)

            data = api.payload
            keys = data.keys()
            if "unit" not in keys:
                data["unit"] = self.config.get(f"general.preferred_vol_units.{dev.device_type}")
            else:
                # TODO make sure the units are supprted
                pass
            if "taken_on" not in keys:
                data["taken_on"] = utcnow_aware()
            meas = DeviceMeasurementsDB.create(db_session, **data)
            return meas.to_dict()