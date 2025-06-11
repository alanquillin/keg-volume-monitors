from db import session_scope
from db.devices import Devices as DevicesDB
from db.device_measurements import DeviceMeasurements as DevicesMeasurementsDB

from lib.time import utcfromtimestamp_aware
from resources import AsyncBaseResource, async_login_required, SWAGGER_AUTHORIZATIONS

from flask_restx import Namespace, fields

api = Namespace('devices_status', description='Device status update', authorizations=SWAGGER_AUTHORIZATIONS)

device_status_mod = api.model("DeviceStatus", {
        "state": fields.Integer(required=True, description=""),
        "latestMeasurement": fields.Float(required=False, description=""),
        "latestMeasurementUnit": fields.Float(required=False, description=""),
        "latestMeasurementTS": fields.Integer(required=False, description=""),
    })
            
@api.route("", "/")
@api.param("id", "The device id")
@api.response(404, 'Device not found')
class DeviceStatus(AsyncBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('device_status', security=["apiKey"])
    @api.expect(device_status_mod, validate=True)
    @async_login_required(allow_service_account=False, require_admin=True)
    async def post(self, id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_with_measurement_stats(db_session, id)
            if not dev:
                api.abort(404)
            
            data = api.payload
            m = data.get("latestMeasurement", 0)
            ts = data.get("latestMeasurementTS", 0)

            if(m > 0 and ts > 0 and dev.latest_measurement != m):
                ts_dt = utcfromtimestamp_aware(ts)
                self.logger.info(f"Latest measurement from device '{dev.name}' did not match latest measurement in DB, adding record.")
                self.logger.debug(f"Adding measurement for device '{dev.name}' ({dev.id}) expected: {dev.latest_measurement} on {dev.latest_measurement_taken_on}, actual: {m} on {ts_dt}")
                m_data = {
                    "device_id": id,
                    "measurement": m,
                    "taken_on": ts_dt
                }
                default_unit = "g" if dev.device_type == "weight" else "ml"
                m_data["unit"] = data.get("latestMeasurementUnit", default_unit)
                
                DevicesMeasurementsDB.create(db_session, **m_data)
            
            st = data["state"]
            self.logger.debug(f"Updating status for device '{dev.name}' ({dev.id}): state = {st}")
            dev = DevicesDB.update(db_session, id, state=st)
            return True