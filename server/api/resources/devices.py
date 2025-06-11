from time import sleep

from db import session_scope
from db.devices import Devices as DevicesDB
from lib import devices
from lib.units import convert_from_ml, convert_to_ml
from lib.util import calculate_volume_ml_from_weight, obj_keys_camel_to_snake, random_string
from resources import AsyncBaseResource, DEVICE_STATE_MAP, async_login_required, SWAGGER_AUTHORIZATIONS

import asyncio
from flask_restx import Namespace, fields, reqparse

api = Namespace('devices', description='Manage devices', authorizations=SWAGGER_AUTHORIZATIONS)

DEVICE_TYPES = ["weight", "flow"]

IN_FIELDS = {
    "name": fields.String( description="The friendly name of the device"),
    "chipId": fields.String(required=True, description="The chip manufacturer's Id for the device"),
    "deviceType": fields.String(required=True, description="The type of device: Options: [weight, flow]"),
    "chipModel": fields.String(required=False, description="The model of the devices chip"),
    "emptyKegWeight": fields.Float(required=False, description=""),
    "emptyKegWeightUnit": fields.String(required=False, description=""),
    "startVolume": fields.Float(required=False, description=""),
    "startVolumeUnit": fields.String(required=False, description=""),
    "displayVolumeUnit": fields.String(required=False, description="The unit to 'display' the measurement values in.  Default = offsetUnit"),
    "state": fields.Integer(required=False, description=""),
    "stateStr": fields.String(required=False, description=""),
    "apiKey": fields.String(required=False, description="")
    # 'meta': fields.String(required=False, description='Optional metadata for the device')
}

new_device_mod = api.model("NewDevice", IN_FIELDS)
device_mod = api.model("Device", {
        "id": fields.String(description="The id of the device", readonly=True),
        "chipType": fields.String(description="The type of controller chip for the device.  Current only supports 'Particle'"),
        "measurementCount": fields.Integer(description=""),
        "latestMeasurement": fields.Float(description=""),
        "latestMeasurementUnit": fields.String(description=""),
        "latestMeasurementTakenOn": fields.DateTime(dt_format="iso8601", description=""),
        "percentRemaining": fields.Float(description="The percent volume remaining"),
        "totalVolumeRemaining": fields.Float(description="Total volume remaining"),
        "online": fields.Boolean(description="")
    } | IN_FIELDS)

class DeviceResource(AsyncBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def get_device_value_in_grams(self, dev, key, unit_key):
        value = dev.get(key, 0)
        unit = dev.get(unit_key, "g")

        if unit != "g":
            #TODO Convert to grams
            pass

        return value
    
    def get_device_value_in_ml(self, dev, key, unit_key):
        value = dev.get(key, 0)
        unit = dev.get(unit_key, "ml")

        if unit != "ml":
            value = convert_to_ml(value, unit)

        return value

    def calculate_and_set_remaining_volume(self, dev):
        if isinstance(dev, list):
            return [self.calculate_and_set_remaining_volume(dev) for dev in dev]
        
        dev_type = dev["deviceType"]
        start_vol_ml = self.get_device_value_in_ml(dev, "startVolume", "startVolumeUnit")
        total_remaining = 0
        percent_remaining = 0

        if dev_type == "weight":
            latest_measurement_g = self.get_device_value_in_grams(dev, "latestMeasurement", "latestMeasurementUnit")
            empty_keg_weight = dev.get("emptyKegWeight", 0)
            if start_vol_ml > 0 and empty_keg_weight > 0 and latest_measurement_g > empty_keg_weight:
                total_remaining = calculate_volume_ml_from_weight(latest_measurement_g - empty_keg_weight)

        else:
            latest_measurement_ml = self.get_device_value_in_ml(dev, "latestMeasurement", "latestMeasurementUnit")
            total_remaining = start_vol_ml - latest_measurement_ml
        
        if total_remaining > 0:
            percent_remaining = total_remaining / start_vol_ml * 100
            displayUnit = dev.get("displayVolumeUnit", "ml")
            if displayUnit != "ml":
                total_remaining= convert_from_ml(total_remaining, displayUnit)
                pass

        dev["percentRemaining"] = round(percent_remaining, 2)
        dev["totalVolumeRemaining"] = round(total_remaining, 2)
        return dev
    
    async def transform_response(self, dev, transform_keys=None, remove_keys=None):
        if isinstance(dev, list):
            return [await self.transform_response(_dev, transform_keys, remove_keys) for _dev in dev]
        
        res = AsyncBaseResource.transform_response(dev, transform_keys=transform_keys, remove_keys=remove_keys)
        res = self.calculate_and_set_remaining_volume(res)
        
        online = await devices.get(dev.chip_id, "online")
        if online is not None:
            res["online"] = online

        res["stateStr"] = DEVICE_STATE_MAP.get(dev.state, "unknown")
        return res
    

@api.route('', '/')
class Devices(DeviceResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('list_devices', security=["apiKey"])
    @api.response(200, 'Success', device_mod)
    @async_login_required(allow_device=False)
    async def get(self):
        with session_scope(self.config) as db_session:
            devices = DevicesDB.get_all_with_measurement_stats(db_session)
            if devices:
                self.logger.debug(f"devices found. results: {devices}")
                return await self.transform_response(devices)
        return []
    
    @api.doc('create_device', security=["apiKey"])
    @api.expect(new_device_mod, validate=True)
    @api.response(201, 'Success', device_mod)
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def post(self):
        with session_scope(self.config) as db_session:
            data = api.payload
            data["chipType"] = "Particle"

            existing_dev = DevicesDB.get_by_chip_id(db_session, data["chipType"], data["chipId"])
            if existing_dev:
                api.abort(400, "Device already exists")

            dev_type = data.get("deviceType", "unknown").lower()
            if dev_type not in DEVICE_TYPES:
                api.abort(400, f"Invalid device type '{dev_type}'.  Supported types are: [weight, flow]")
            
            keys = data.keys()
            if dev_type == "weight":
                if "emptyKegWeight" not in keys:
                    data["emptyKegWeight"] = 0
                
                if "emptyKegWeighUnit" not in keys:
                    data["emptyKegWeightUnit"] = "g"
            
            if "startVolume" not in keys:
                data["startVolume"] = 0
            
            if "startVolumeUnit" not in keys:
                data["startVolumeUnit"] = "ml"
            
            if "displayUnit" not in keys:
                data["displayVolumeUnit"] = self.config.get(f"general.preferred_vol_units.{dev_type}")

            if "apiKey" not in keys:
                data["apiKey"] = random_string(self.config.get("general.default_api_key_length"))
            
            if "name" not in keys:
                self.logger.debug(f"Name was not provided for new device, attempting to pull device name from the cloud.  chip type: {data['chipType']}, chip id: {data['chipId']}, chip model: {data.get('chipModel', 'UNKNOWN')}")
                name = "UNKNOWN"
                try:
                    details = await devices.get_details(data["chipId"])
                    if details:
                        name = details.get("name", name)
                except:
                    self.logger.error(f"unable to retrieve name for device.  chip type: {data['chipType']}, chip id: {data['chipId']}, chip model: {data.get('chipModel', 'UNKNOWN')}")
                data["name"] = name
            
            self.logger.debug(f"Creating device record with data: {data}")
            dev = DevicesDB.create(db_session, **obj_keys_camel_to_snake(data))
            return await self.transform_response(dev)

@api.route('/find')
@api.response(404, 'Device not found')
class FindDevice(DeviceResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('find_device', security=["apiKey"])
    @api.response(200, 'Success', device_mod)
    @api.param('chip_id', 'The device chip_type id', _in="query")
    @api.param('chip_type', 'The device chip_type.  Currently only supports "Particle"', _in="query")
    @async_login_required()
    async def get(self):
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
                self.logger.debug(f"found device(s) matching chip type: {chip_type} with chip id: {chip_id}, results: {devs}")
                return await self.transform_response(devs)
        api.abort(404)

@api.route('/<id>')
@api.param('id', 'The device id')
@api.response(404, 'Device not found')
class Device(DeviceResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('get_device', security=["apiKey"])
    @async_login_required(allow_device=False)
    @api.response(200, 'Success', device_mod)
    async def get(self, id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_with_measurement_stats(db_session, id)
            if dev:
                self.logger.debug(f"Device found: {dev}")
                return await self.transform_response(dev)
        api.abort(404)

    @api.doc('patch_device', security=["apiKey"])
    @api.expect(new_device_mod, validate=False)
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    #@api.marshal_with(device_mod)
    async def patch(self, id):
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

            self.logger.debug(f"PATCH data for {id}: JSON data {data}")
            u_data = obj_keys_camel_to_snake(data)
            self.logger.debug(f"Updating device {id} with data {u_data}")
        
            dev = DevicesDB.update(db_session, id, **u_data)
            return await self.transform_response(dev)
        
    @api.doc('delete_device', security=["apiKey"])
    @async_login_required(allow_device=False, allow_service_account=False, require_admin=True)
    async def delete(self, id):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, id)
            if not dev:
                api.abort(404)
            DevicesDB.delete(db_session, id)
            return True
        

@api.route("/<id>/rpc/<func_name>")
@api.param("id", "The device id")
@api.param('func_name', "the name of the function to execute")
@api.response(404, 'Device not found')
class DeviceRPC(DeviceResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('device_rpc_execute', security=["apiKey"])
    @async_login_required(allow_device=False, require_admin=True)
    async def post(self, id, func_name):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, id)
            if not dev:
                api.abort(404)
            chip_id = dev.chip_id
        
        if func_name in ["ping", "start_calibration", "cancel_calibration", "calibrate", "tare", "clear_memory", "send_most_recent_sample", "start_maintenance_mode", "stop_maintenance_mode"]:
            data = {} 
            if func_name == "calibrate":
                parser = api.parser()
                parser.add_argument('calibrationWeight', type=float, location='json')
                args = parser.parse_args()
                cal_weight = args.get("calibrationWeight")
                if not cal_weight:
                    self.logger.warning("Calibration RPC was called but could not find the calibration value in the request")
                    self.logger.debug(f"Args: {args}")
                    api.abort(400, "calibrationWeight value is required but was not provided") 
                data["cal_weight"] = cal_weight
            val, err, err_code = await devices.run(chip_id, func_name, **data)
            self.logger.debug(f"Executed device function (chip id: {chip_id}) complete: val = {val}, err = {err}, err_code = {err_code}")

            if err: 
                api.abort(err_code, err)
            if val == -99: 
                self.logger.info(f"Executed device function '{func_name}' successfully but the device failed to push status.  Attempting to pull latest state")
                st, err2, err2_code = await devices.pull_state(chip_id)
                self.logger.debug(f"Device state pull complete: val = {st}, err = {err2}, err_code = {err2_code}")
                if err2 is None:
                    self.logger.debug(f"Updating device state ={st}")
                    with session_scope(self.config) as db_session:
                        dev = DevicesDB.update(db_session, id, **{"state": st})
                        self.logger.debug(f"Device state update complete")
            
            with session_scope(self.config) as db_session:
                self.logger.debug(f"Retrieving device data again to return")
                dev = DevicesDB.get_with_measurement_stats(db_session, id)
                return await self.transform_response(dev) 
        else:
            api.abort(405, "Unsupported RPC function")


@api.route("/<id>/manufacturer_info/<key>")
@api.route("/<id>/manufacturer_info")
@api.param("id", "The device id")
@api.param('key', "the name of optional data key.  If not provided, all available manufacturer data will be returned")
@api.response(404, 'Device not found')
class DeviceManufacturerInfo(AsyncBaseResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @api.doc('device_manufacturer_info', security=["apiKey"])
    @async_login_required(allow_service_account=False, require_admin=True)
    async def get(self, id, key=None):
        with session_scope(self.config) as db_session:
            dev = DevicesDB.get_by_pkey(db_session, id)
            if not dev:
                api.abort(404)
            chip_id = dev.chip_id

        if not key:
            return await devices.get(chip_id, "get_details")
        elif key in ["get_details", "get_description", "supports_status_check", "online"]:
            return await devices.get(chip_id, key)
        else:
            details = await devices.get(chip_id, "get_details")
            if not details:
                return None
            keys = details.keys()
            if key not in keys:
                api.abort(400, "Unsupported key function")
            return details.get(key)