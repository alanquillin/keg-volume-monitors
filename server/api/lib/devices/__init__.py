from lib import logging
from lib.devices import particle

LOG = logging.getLogger(__name__)

device_data_functions = {
    "particle": {
        "_default_": {
            "get_details": particle.get_details,
            "get_description": particle.get_description,
            "supports_status_check": particle.supports_status_check,
            "online": particle.online,
        }
    }
}

device_action_functions = {
    "particle": {
        "_default_": {
            "ping": particle.ping,
            "start_calibration": particle.start_calibration,
            "cancel_calibration": particle.cancel_calibration,
            "calibrate": particle.calibrate,
            "tare": particle.tare,
            "clear_memory": particle.clear_memory,
            "send_most_recent_sample": particle.send_most_recent_sample,
            "start_maintenance_mode": particle.start_maintenance_mode,
            "stop_maintenance_mode": particle.stop_maintenance_mode,
            "pull_state": particle.pull_state
        }
    }
}


async def _execute(func_name, func_set, device, *args, **kwargs):
    # chip_type = device.chip_type.lower()
    chip_type = "particle"
    # model = device.chip_model
    # if model:
    #     model = model.lower()

    n = None, None, None
    funcs = func_set.get(chip_type)
    if not funcs:
        LOG.info("no functions configured for devices with chip type: %s", chip_type)
        return n

    funcs = funcs.get("_default_")
    # if model:
    #     model_funcs = funcs.get(model)
    #     if model_funcs:
    #         m_funcs = funcs | model_funcs
    #         funcs = m_funcs

    # if not funcs:
    #     LOG.info("no functions configured for %s devices with model: %s", chip_type, model)
    #     return n

    fn = funcs.get(func_name)
    if not fn:
        # LOG.info("no %s function configured for %s devices with model: %s", func_name, chip_type, model)
        LOG.info("no %s function configured for %s devices", func_name, chip_type)
        return n

    return await fn(device, *args, **kwargs)


async def run(device, func_name, *args, **kwargs):
    return await _execute(func_name, device_action_functions, device, *args, **kwargs)


async def get(device, func_name, *args, **kwargs):
    return await _execute(func_name, device_data_functions, device, *args, **kwargs)


async def ping(device, *args, **kwargs):
    return await run(device, "ping", *args, **kwargs)


async def get_details(device, *args, **kwargs):
    return await get(device, "get_details", *args, **kwargs)


async def get_description(device, *args, **kwargs):
    return await get(device, "get_description", *args, **kwargs)


def supports_status_check(device, *args, **kwargs):
    # There is a chance the implementation return None or other falsey values, so explicitely check for True
    return True if get(device, "supports_status_check", *args, **kwargs) == True else False

async def start_calibration(device, *args, **kwargs):
    return await run(device, "start_calibration")

async def calibrate(device, cal_weight, *args, **kwargs):
    return await run(device, "calibrate", cal_weight)

async def tare(device, *args, **kwargs):
    return await run(device, "tare")

async def clear_memory(device, *args, **kwargs):
    return await run(device, "clear_memory")

async def send_most_recent_sample(device,  *args, **kwargs):
    return await run(device, "send_most_recent_sample")

async def start_maintenance_mode(device, *args, **kwargs):
    return await run(device, "start_maintenance_mode")

async def stop_maintenance_mode(device, *args, **kwargs):
    return await run(device, "stop_maintenance_mode")

async def pull_state(device, *args, **kwargs):
    return await run(device, "pull_state")