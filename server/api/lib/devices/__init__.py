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
            "calibrate": particle.calibrate,
            "tare": particle.tare,
            "clear_memory": particle.clear_memory,
            "send_most_recent_sample": particle.send_most_recent_sample,
            "start_maintenance_mode": particle.start_maintenance_mode,
            "stop_maintenance_mode": particle.stop_maintenance_mode
        }
    }
}


def _execute(func_name, func_set, device, *args, **kwargs):
    chip_type = device.chip_type.lower()
    model = device.chip_model
    if model:
        model = model.lower()

    funcs = func_set.get(chip_type)
    if not funcs:
        LOG.info("no functions configured for devices with chip type: %s", chip_type)
        return

    funcs = funcs.get("_default_")
    if model:
        model_funcs = funcs.get(model)
        if model_funcs:
            m_funcs = funcs | model_funcs
            funcs = m_funcs

    if not funcs:
        LOG.info("no functions configured for %s devices with model: %s", chip_type, model)
        return

    fn = funcs.get(func_name)
    if not fn:
        LOG.info("no %s function configured for %s devices with model: %s", func_name, chip_type, model)
        return

    return fn(device, *args, **kwargs)


def run(device, func_name, *args, **kwargs):
    return _execute(func_name, device_action_functions, device, *args, **kwargs)


def get(device, func_name, *args, **kwargs):
    return _execute(func_name, device_data_functions, device, *args, **kwargs)


def ping(device, *args, **kwargs):
    return run(device, "ping", *args, **kwargs)


def get_details(device, *args, **kwargs):
    return get(device, "get_details", *args, **kwargs)


def get_description(device, *args, **kwargs):
    return get(device, "get_description", *args, **kwargs)


def supports_status_check(device, *args, **kwargs):
    # There is a chance the implementation return None or other falsey values, so explicitely check for True
    return True if get(device, "supports_status_check", *args, **kwargs) == True else False

def start_calibration(device, *args, **kwargs):
    return run(device, "start_calibration")

def calibrate(device, cal_weight, *args, **kwargs):
    return run(device, "calibrate", cal_weight)

def tare(device, *args, **kwargs):
    return run(device, "tare")

def clear_memory(device, *args, **kwargs):
    return run(device, "clear_memory")

def send_most_recent_sample(device,  *args, **kwargs):
    return run(device, "send_most_recent_sample")

def start_maintenance_mode(device, *args, **kwargs):
    return run(device, "start_maintenance_mode")

def stop_maintenance_mode(device, *args, **kwargs):
    return run(device, "stop_maintenance_mode")