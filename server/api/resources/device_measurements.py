from datetime import datetime

from db import session_scope
from db.devices import Devices as DevicesDB
from db.device_measurements import DeviceMeasurements as DeviceMeasurementsDB
from lib.time import utcnow_aware, utcfromtimestamp_aware
from resources import AsyncBaseResource

from flask_restx import Namespace, Resource, fields

api = Namespace('device_measurements', description='Manage Device Measurements')

save_device_measurement_mod = api.model('SaveDeviceMeasurement', {
    'm': fields.Float(required=True, description='The value of the taken measurement'),
    'u': fields.String(required=False, description='The unit of the taken measurement.  If not provided, the unit the device was calibrated with is used, else the default unit for the given device type'),
    "ts": fields.Integer(requires=False, description="The timestamp that the measurement was taken.  If not provided, the the timestamp fo the request is used.")
})
device_measurement_mod = api.model('DeviceMeasurement', {
    'id': fields.String(required=True, description='The id of the device', readonly=True),
    'deviceId': fields.String(required=True, description="The device Id"),
    'measurement': fields.Float(required=True, description='The value of the taken measurement'),
    'unit': fields.String(required=False, description='The unit of the taken measurement'),
    "takenOn": fields.DateTime(requires=False, description="The datetime that the measurement was taken.")
})

@api.route('', '/')
class DeviceMeasurements(AsyncBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('list_device_measurements')
    #@api.marshal_list_with(device_measurement_mod)
    async def get(self, device_id):
        with session_scope(self.config) as db_session:
            measurements = DeviceMeasurementsDB.query(db_session, device_id=device_id)
            if measurements:
                return self.transform_response(measurements)
        return []
    
    @api.doc('save_device_measurement')
    @api.expect(save_device_measurement_mod, validate=True)
    #@api.marshal_list_with(device_measurement_mod, code=201)
    async def post(self, device_id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, device_id)
            if not dev:
                api.abort(404)

            data = api.payload
            keys = data.keys()
            if "u" not in keys:
                # TODO once the calibration units are stored for the device, we need to first try and use that and then fall back to the config default
                data["u"] = "g" if dev.device_type == "weight" else "ml"
            else:
                # TODO make sure the units are supported
                pass

            measurement= {
                "device_id": device_id,
                "measurement": data["m"],
                "unit": data["u"]
            }

            if "ts" in keys:
                measurement["taken_on"] = utcfromtimestamp_aware(data["ts"])
            else:
                measurement["taken_on"] = utcnow_aware()
            
            meas = DeviceMeasurementsDB.create(db_session, **measurement)
            return self.transform_response(meas)