#include "service.h"
#include <HttpClient.h>

Logger logger("app.service");

HttpClient http_client;

String programToDBVal(uint8_t program){
    String sProg = programToString(program);
    sProg.toLowerCase().replace(" ", "_");
    return sProg;
}

/**
* Constructor.
*/
DataService::DataService() {}

DataService::DataService(bool enabled, String manufacturer, String manufacturerId, String deviceType, int port, String hostname = "", String ipAddress = "", bool secure=False, int maxRetries=3) {
    _enabled = enabled;
    _manufacturer = manufacturer;
    _manufacturerId = manufacturerId;
    _deviceType = deviceType;
    _hostname = hostname;
    _ipAddress = ipAddress;
    _port = port;
    _maxRetries = maxRetries;

    if (secure) {
        _scheme = "https"
    } else {
        _scheme = "http"
    }
}

DataService::begin() {}

DataService::begin(bool enabled, String manufacturer, String manufacturerId, String deviceType, int port, String hostname = "", String ipAddress = "", bool secure=False, int maxRetries=3) {
    _enabled = enabled;
    _manufacturer = manufacturer;
    _manufacturerId = manufacturerId;
    _deviceType = deviceType;
    _hostname = hostname;
    _ipAddress = ipAddress;
    _port = port;
    _maxRetries = maxRetries;

    if (secure) {
        _scheme = "https"
    } else {
        _scheme = "http"
    }
}

bool DataService::ping() {
    if (!_enabled) {
        return true;
    }

    int cnt = 0;
    while(cnt < _maxRetries){
        http_response_t response = _get("/health");
        if (response.status == 200){
            return true;
        }
        cnt = cnt + 1;
    }
    return false;
}

device_data_t DataService::getDeviceData(String id) {
    if (!_enabled) {
        return {true};
    }
    
    DynamicJsonDocument doc = _getJson("/api/v1/devices/" + id, 1024);
    return _parseDeviceData(doc);
}

device_data_t DataService::findDevice(String manufacturerId) {
    if (!_enabled) {
        return {true};
    }
    
    String path = "/api/v1/devices/find?manufacturer=";
    path.concat(_manufacturer);
    path.concat("&manufacturer_id=");
    path.concat(manufacturerId);
    
    DynamicJsonDocument doc = _getJson(path, 1024);

    JsonArray array = doc.as<JsonArray>();
    if (array.size() == 0) {
        return {true};
    }
    return _parseDeviceData(array[0]);
}

device_data_t DataService::registerDevice(String manufacturerId, double targetTemp, double calibrationDiff, uint8_t program, double coolDiff, double heatDiff, double tempPrecision){
    if (!_enabled) {
        return {true};
    }

    String path = "/api/v1/devices";

    const uint16_t docSize = 1024;
    DynamicJsonDocument jData(docSize);
    jData["manufacturer_id"] =  _manufacturerId.c_str();
    jData["manufacturer"] = _manufacturer.c_str();
    jData["device_type"] = _deviceType.c_str();

    device_data_t res = {true};
    int cnt = 0;
    while(cnt < _maxRetries){
        http_response_t response = _post(path, jData, docSize);
        if (response.status < 300){
            return _parseDeviceData(_respToJson(response, 1024));
        }
        cnt = cnt + 1;
    }
    return res;
}

bool DataService::sendStats(String id, float measurement, long timestamp, uint8_t size){
    if (!_enabled) {
        return true;
    }

    String path = "/api/v1/devices/" + id + "/measurements";

    const uint16_t docSize = 384;
    DynamicJsonDocument jData(docSize);
    jData["m"] =  measurement;
    jData["ts"] =  timestamp;

    int cnt = 0;
    while(cnt < _maxRetries){
        http_response_t response = _post(path, jData, docSize);
        if (response.status < 300) {
            return true;
        }
        cnt = cnt + 1;
    }
    return false;
}

DynamicJsonDocument DataService::_getJson(String path, uint16_t docSize) {
    return _respToJson(_get(path), docSize);
}

http_response_t DataService::_get(String path) {
    return _get(_buildRequest(path));
}

http_response_t DataService::_get(http_request_t request){
    http_response_t response;

    logger.trace("GET %s://%s:%d%s", _scheme.c_str(), request.hostname.c_str(), request.port, request.path.c_str());

    http_header_t headers[] = {
        { "Accept" , "application/json" },
        { NULL, NULL } // NOTE: Always terminate headers will NULL
    };
    http_client.get(request, response, headers);

    logger.trace("Response status: %d", response.status);
    logger.trace("Response Body: %s", response.body.c_str());

    return response;
}

http_response_t DataService::_post(String path, DynamicJsonDocument jDoc, const uint16_t docSize){
    return _post(_buildRequest(path, jDoc, docSize));
}

http_response_t DataService::_post(http_request_t request){
    http_response_t response;

    logger.trace("POST %s://%s:%d%s", _scheme.c_str(), request.hostname.c_str(), request.port, request.path.c_str());
    logger.trace("Data: %s", request.body.c_str());

    http_header_t headers[] = {
        { "Content-Type", "application/json" },
        { "Accept" , "application/json" },
        { NULL, NULL } // NOTE: Always terminate headers will NULL
    };
    http_client.post(request, response, headers);

    logger.trace("Response status: %d", response.status);
    logger.trace("Response Body: %s", response.body.c_str());
    
    return response;
}

http_request_t DataService::_buildRequest(String path) {
    http_request_t request;
    request.hostname = _hostname;
    request.port = _port;
    request.path = path;
    return request;
}

http_request_t DataService::_buildRequest(String path, DynamicJsonDocument jDoc, const uint16_t docSize) {
    char data[1024];
    serializeJson(jDoc, data);
    http_request_t request = _buildRequest(path);
    request.body = data;
    return request
}

DynamicJsonDocument DataService::_respToJson(http_response_t response, const uint16_t docSize) {
    DynamicJsonDocument doc(docSize);
    if (response.status == 200){
        DeserializationError error = deserializeJson(doc, response.body.c_str());
        if (error) {
            logger.error("deserializeJson() failed: ");
            // DO SOMETHING TO THROW AN ERROR 
        }
    }

    return doc;
}

device_data_t DataService::_parseDeviceData(DynamicJsonDocument jDoc) {
    device_data_t res = {true};
    if (!jDoc.isNull()) {
        res.isNull = false;
        JsonObject deviceDetails = jDoc.as<JsonObject>();
        res.id = String(deviceDetails["id"].as<const char*>());
        res.manufacturerId = String(deviceDetails["manufacturer_id"].as<const char*>());
        res.deviceType = String(deviceDetails["device_type"].as<const char*>());
    }
    return res;
}
