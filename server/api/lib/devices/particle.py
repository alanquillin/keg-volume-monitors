from lib import logging
from lib.config import Config

import aiohttp

CONFIG = Config()

LOG = logging.getLogger(__name__)

BASE_URL = CONFIG.get("particle.base_url", "https://api.particle.io")

PARTICLE_CLOUD_FN = {
    "initCalibration": {
        "errors": {}
    },
    "cancelCalibration": {
        "errors": {
            -1: {"msg": "Calibration is in progress and cannot be cancelled"},
            -2: {"msg": "Initial calibration has not completed."}
        }
    }, 
    "calibrate": {
        "errors": {
            -1: {"msg": "Invalid calibration value.  Requires a float", "code": 400},
        }
    }, 
    "tare": {
        "errors": {}
    }, 
    "clearMemory": {
        "errors": {}
    },
    "sendStatus": {
        "errors": {
            -1: {"msg": "Failed to push status"},
            -2: {"msg": "Unable to retrieve extended device information"},
            -3: {"msg": "No samples"}
        }
    },
    "startMaintenanceMode": {
        "errors": {}
    },
    "stopMaintenanceMode": {
        "errors": {}
    }
}

def _req(fn):
    def wrapper(device_chip_id, path, **kwargs):
        api_key = CONFIG.get("particle.api_key")

        if not api_key:
            LOG.warning("Alerts are enabled for Particle device, but no API key was provided.")
            return

        headers = {"Authorization": f"Bearer {api_key}"}
        url = f"{BASE_URL}/v1/devices/{device_chip_id}{path}"
        return fn(device_chip_id, url, headers=headers, **kwargs)

    return wrapper


@_req
async def _get(device_chip_id, uri, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(uri, **kwargs) as response:
            return response.status, await response.json()


@_req
async def _post(device_chip_id, uri, **kwargs):
    async with aiohttp.ClientSession() as session:
        async with session.post(uri, **kwargs) as response:
            return response.status, await response.json()


def _enabled():
    return CONFIG.get("particle.device_services.enabled", False)


def _particle_func(fn):
    def wrapper(*args, **kwargs):
        enabled = _enabled()

        if not enabled:
            LOG.info("Services are not enabled for Particle devices.")
            return

        return fn(*args, **kwargs)

    return wrapper


@_particle_func
async def ping(device_chip_id):
    try:
        resp_code, data = await _post(device_chip_id, "/ping")
        return data.get("online", False)
    except Exception as ex:
        print(ex)
        return False


@_particle_func
async def get_details(device_chip_id, *args, **kwargs):
    try:
        resp_code, data = await _get(device_chip_id, "")
        return data
    except Exception as ex:
        LOG.exception("There was an error trying to execute the cloud function for device chip id: %s", device_chip_id)


@_particle_func
async def get_description(device_chip_id, *args, **kwargs):
    try:
        details = await get_details(device_chip_id, *args, **kwargs)
        if not details:
            return

        return details.get("name")
    except Exception as ex:
        LOG.exception("There was an error trying to execute the cloud function for device chip id: %s", device_chip_id)


async def supports_status_check(*args, **kwargs):
    return _enabled()

@_particle_func
async def start_calibration(device_chip_id, *args, **kwargs):
    return await _call_func(device_chip_id, "initCalibration")

@_particle_func
async def cancel_calibration(device_chip_id, *args, **kwargs):
    return await _call_func(device_chip_id, "cancelCalibration")

@_particle_func
async def calibrate(device_chip_id, cal_weight, *args, **kwargs):
    return await _call_func(device_chip_id, "calibrate", cal_weight)

@_particle_func
async def tare(device_chip_id, *args, **kwargs):
    return await _call_func(device_chip_id, "tare")

@_particle_func
async def clear_memory(device_chip_id, *args, **kwargs):
    return await _call_func(device_chip_id, "clearMemory")

@_particle_func
async def send_most_recent_sample(device_chip_id,  *args, **kwargs):
    return await _call_func(device_chip_id, "sendMostRecentSample")

@_particle_func
async def start_maintenance_mode(device_chip_id, *args, **kwargs):
    return await _call_func(device_chip_id, "startMaintenanceMode")

@_particle_func
async def stop_maintenance_mode(device_chip_id, *args, **kwargs):
    return await _call_func(device_chip_id, "stopMaintenanceMode")

@_particle_func
async def pull_state(device_chip_id, *args, **kwargs):
    return await _call_func(device_chip_id, "getState")

async def _call_func(device_chip_id, func, data=None):
    try:
        kwargs = {}
        if data is not None:
            kwargs["json"] = {"arg": f"{data}"}
        status_code, data = await _post(device_chip_id, f"/{func}", **kwargs)
        LOG.debug("RESPONSE (%s): <%s> %s", func, status_code, data)

        if status_code != 200:
            return False, None, None
        
        ret_value = data.get("return_value")

        err_msg = None
        err_code = None
        if ret_value != -99 and ret_value < 0:
            err = PARTICLE_CLOUD_FN.get(func, {}).get("errors", {}).get(ret_value, {})
            err_msg = err.get("msg", f"Unknown error code: {ret_value}")
            err_code = err.get("code", 424)

        return ret_value, err_msg, err_code

    except Exception as ex:
        LOG.exception("There was an error trying to execute the cloud function for device chip id: %s", device_chip_id)


async def online(device_chip_id, *args, **kwargs):
    details = await get_details(device_chip_id, *args, **kwargs)
    if not details:
        return False
    return details.get("online", False)
