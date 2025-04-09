from db import session_scope
from db.devices import Devices as DevicesDB

from resources import BaseResource
from flask_restx import Namespace, Resource, fields, reqparse, inputs
from flask_restx.utils import camel_to_dash

api = Namespace('devices', description='Manage devices')

DEVICE_TYPES = ["weight", "flow"]

IN_FIELDS = {
    'name': fields.String(required=True, description="The friendly name of the device"),
    'chipId': fields.String(required=True, description="The chip manufacturer's Id for the device"),
    'deviceType': fields.String(required=True, description="The type of device: Options: [weight, flow]"),
    'chipModel': fields.String(required=False, description="")
    # 'meta': fields.String(required=False, description='Optional metadata for the device')
}

new_device_mod = api.model('NewDevice', IN_FIELDS)
device_mod = api.model('Device', {
        'id': fields.String(required=True, description="The id of the device", readonly=True),
        'chipType': fields.String(required=True, description="The type of controller chip for the device.  Current only supports 'Particle'")
    } | IN_FIELDS)

@api.route('/')
class Devices(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('list_devices')
    @api.marshal_list_with(device_mod)
    def get(self):
        with session_scope(self.config) as db_session:
            devices = DevicesDB.query(db_session)
            if devices:
                return self.transform_response(devices)
        return []
    
    @api.doc('create_device')
    @api.expect(new_device_mod, validate=True)
    @api.marshal_with(device_mod, code=201)
    def post(self):
        with session_scope(self.config) as db_session:
            data = api.payload
            data["chipType"] = "Particle"

            existing_dev = DevicesDB.get_by_chip_id(db_session, data["chipType"], data["chipId"])
            if existing_dev:
                api.abort(400, "Device already exists")

            dev_type = data.get("deviceType", "unknown").lower()
            if dev_type not in DEVICE_TYPES:
                api.abort(400, f"Invalid device type '{dev_type}'.  Supported types are: [weight, flow]")
            
            dev = DevicesDB.create(db_session, **camel_to_dash(data))
            return self.transform_response(dev)

@api.route('/find')
@api.response(404, 'Device not found')
class FindDevice(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('find_device')
    @api.param('chip_id', 'The device chip_type id', _in="query")
    @api.param('chip_type', 'The device chip_type.  Currently only supports "Particle"', _in="query")
    @api.marshal_list_with(device_mod)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('chip_id', location='args', required=True)
        parser.add_argument('chip_type', location='args')
        args = parser.parse_args()
        self.logger.debug(f"args: {args}")
        
        chip_type = args.get("chip_type")
        chip_id = args.get("chip_id")
        if not chip_type:
            chip_type = "Particle"
        elif chip_type.lower() != "particle":
            api.abort(400, "Invalid chip_type.  Currently only 'Particle' is supported")

        with session_scope(self.config) as db_session:
            devs = DevicesDB.get_by_chip_id(db_session, chip_type, chip_id)
            if devs:
                return self.transform_response(devs)
        api.abort(404)

@api.route('/<id>')
@api.param('id', 'The device id')
@api.response(404, 'Device not found')
class Device(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('get_device')
    @api.marshal_with(device_mod)
    def get(self, id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, id)
            if dev:
                return self.transform_response(dev)
        api.abort(404)

    @api.doc('patch_device')
    @api.expect(new_device_mod, validate=False)
    @api.marshal_list_with(device_mod, code=201)
    def patch(self, id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, id)
            if not dev:
                api.abort(404)
            data = api.payload
            keys = data.keys()
            if "chipType" in keys:
                ct = data.get("chipType")
                if ct != "Particle":
                    api.abort(400, f"Invalid chip_type '{ct}'.  Currently only Particle devices are supported.")
            if "deviceType" in keys:
                dt = data.get("deviceType", "unknown").lower()
                if dt not in DEVICE_TYPES:
                    api.abort(400, f"Invalid device type '{dt}'.  Supported types are: [weight, flow]")
            dev = DevicesDB.update(db_session, id, **camel_to_dash(data))
            return self.transform_response(dev)
        
    @api.doc('delete_device')
    def delete(self, id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, id)
            if not dev:
                api.abort(404)
            DevicesDB.delete(db_session, id)
            return True