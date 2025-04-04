from resources import BaseResource
from flask_restx import Namespace, Resource, fields

api = Namespace('devices', description='Manage devices')

device_mod = api.model('Device', {
    'id': fields.String(required=True, description='The id of the device'),
    'name': fields.String(required=True, description='The friendly name of the device'),
    'type': fields.String(required=True, description='The type of device')
})

TEST_DEVICES = [
    {'id': 'abc123', 'name': 'my test device', 'type': 'weight'},
]

@api.route('/')
class Devices(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('list_devices')
    @api.marshal_list_with(device_mod)
    def get(self):
        return TEST_DEVICES

@api.route('/<id>')
@api.param('id', 'The device id')
@api.response(404, 'Device not found')
class Device(BaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('get_device')
    @api.marshal_with(device_mod)
    def get(self, id):
        for dev in TEST_DEVICES:
            if dev['id'] == id:
                return dev
        api.abort(404)