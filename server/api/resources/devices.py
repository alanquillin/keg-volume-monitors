from db import session_scope
from db.devices import Devices as DevicesDB

from resources import BaseResource
from flask_restx import Namespace, Resource, fields, reqparse, inputs

api = Namespace('devices', description='Manage devices')

DEVICE_TYPES = ["weight", "flow"]

IN_FIELDS = {
    'name': fields.String(required=True, description='The friendly name of the device'),
    'manufacturer_id': fields.String(required=True, description='The manufacturers Id for the device'),
    'device_type': fields.String(required=True, description='The type of device: Options: [weight, flow]')
    # 'meta': fields.String(required=False, description='Optional metadata for the device')
}

new_device_mod = api.model('NewDevice', IN_FIELDS)
device_mod = api.model('Device', {
        'id': fields.String(required=True, description='The id of the device', readonly=True),
        'manufacturer': fields.String(required=True, description='The manufacturer of the device')
    } | IN_FIELDS)

@api.route('/')
class Devices(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('list_devices')
    @api.marshal_list_with(device_mod)
    def get(self):
        d = []
        with session_scope(self.config) as db_session:
            devices = DevicesDB.query(db_session)
            if devices:
                for dev in devices:
                    d.append(dev.to_dict())
        return d
    
    @api.doc('create_device')
    @api.expect(new_device_mod, validate=True)
    @api.marshal_list_with(device_mod, code=201)
    def post(self):
        with session_scope(self.config) as db_session:
            data = api.payload
            data["manufacturer"] = "Particle"

            existing_dev = DevicesDB.get_by_manufacturer_id(db_session, data["manufacturer"], data["manufacturer_id"])
            if existing_dev:
                api.abort(400, "Device already exists")

            dev_type = data.get("device_type", "unkown").lower()
            if dev_type not in DEVICE_TYPES:
                api.abort(400, f"Invalid device type '{dev_type}'.  Supported types are: [weight, flow]")
            dev = DevicesDB.create(db_session, **data)
            return dev.to_dict()

@api.route('/find')
@api.response(404, 'Device not found')
class FindDevice(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('find_device')
    @api.param('manufacturer_id', 'The device manufacturer id', _in="query")
    @api.param('manufacturer', 'The device manufacturer.  Currently only supports "Particle"', _in="query")
    @api.marshal_with(device_mod)
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('manufacturer_id', location='args', required=True)
        parser.add_argument('manufacturer', location='args')
        args = parser.parse_args()
        self.logger.debug(f"args: {args}")
        
        manufacturer = args.get("manufacturer")
        manufacturer_id = args.get("manufacturer_id")
        if not manufacturer:
            manufacturer = "Particle"
        elif manufacturer.lower() != "particle":
            api.abort(400, "Invalid manufacturer.  Currently only 'Particle' is supported")

        with session_scope(self.config) as db_session:
            devs = DevicesDB.get_by_manufacturer_id(db_session, manufacturer, manufacturer_id)
            if devs:
                return [d.to_dict() for d in devs]
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
                return dev.to_dict()
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
            if "manufacturer" in keys:
                manu = data.get("manufacturer")
                if manu != "Particle":
                    api.abort(400, f"Invalid manufacturer '{manu}'.  Currently only Particle devices are supported.")
            if "device_type" in keys:
                dev_type = data.get("device_type", "unkown").lower()
                if dev_type not in DEVICE_TYPES:
                    api.abort(400, f"Invalid device type '{dev_type}'.  Supported types are: [weight, flow]")
            dev = DevicesDB.update(db_session, id, **data)
            return dev.to_dict()
        
    @api.doc('delete_device')
    def delete(self, id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, id)
            if not dev:
                api.abort(404)
            DevicesDB.delete(db_session, id)
            return True