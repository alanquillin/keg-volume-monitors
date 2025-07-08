#include "config.h"
#include "service.h"
#include <HttpClient.h>
#include "Base64RK.h"

Logger logger("app.service");

HttpClient http_client;

const String CHIP_TYPE = "Particle";

/**
* Constructor.
*/
DataService::DataService(bool enabled, String deviceType, String hostname, int port, String apiKey, bool secure, int maxRetries) {
    _enabled = enabled;
    _deviceType = deviceType;
    _hostname = hostname;
    _port = port;
    _maxRetries = maxRetries;
    _generateBearerToken(apiKey);

    if (secure) {
        _scheme = "https";
    } else {
        _scheme = "http";
    }
}

bool DataService::ping() {
    if (!_enabled) {
        return true;
    }

    int cnt = 0;
    while(cnt < _maxRetries){
        http_response_t response = _get("/api/v1/ping");
        if (response.status == 200){
            return true;
        }
        cnt = cnt + 1;
    }
    return false;
}

device_data_t DataService::findDevice() {
    if (!_enabled) {
        return {true};
    }
    
    String path = "/api/v1/devices/find?chip_type=";
    path.concat(CHIP_TYPE);
    path.concat("&chip_id=");
    path.concat(System.deviceID());
    
    http_response_t response = _get(path);
    JsonDocument doc = _respToJson(response);


    JsonArray array = doc.as<JsonArray>();
    if (array.size() == 0) {
        return {true};
    }
    return _parseDeviceData(array[0]);
}

device_data_t DataService::registerDevice(){
    if (!_enabled) {
        return {true};
    }

    String path = "/api/v1/devices";

    JsonDocument jData;
    jData["chipId"] =  System.deviceID().c_str();
    jData["chipType"] = CHIP_TYPE.c_str();
    jData["deviceType"] = _deviceType.c_str();
    jData["chipModel"] = CHIP_MODEL.c_str();

    device_data_t res = {true};
    int cnt = 0;
    while(cnt < _maxRetries){
        http_response_t response = _post(path, jData);
        if (response.status >= 100 && response.status < 300){
            return _parseDeviceData(_respToJson(response));
        }
        cnt = cnt + 1;
    }
    return res;
}

bool DataService::sendMeasurement(String id, float measurement, long timestamp){
    if (!_enabled) {
        return true;
    }

    String path = "/api/v1/devices/" + id + "/measurements";

    JsonDocument jData;
    jData["m"] =  measurement;
    jData["ts"] =  timestamp;

    int cnt = 0;
    while(cnt < _maxRetries){
        http_response_t response = _post(path, jData);
        if (response.status >= 100 && response.status < 300) {
            return true;
        }
        cnt = cnt + 1;
    }
    return false;
}

bool DataService::sendStatus(device_status_t status){
    if (!_enabled) {
        return true;
    }

    String path = "/api/v1/devices/" + status.id + "/status";

    JsonDocument jData;
    jData["latestMeasurement"] =  status.latestMeasurement;
    jData["latestMeasurementTS"] =  status.latestMeasurementTS;
    jData["state"] =  status.state;
    jData["emptyKegWeightGrams"] = status.emptyKegWeight;

    int cnt = 0;
    while(cnt < _maxRetries){
        http_response_t response = _post(path, jData);
        if (response.status >= 100 && response.status < 300) {
            return true;
        }
        cnt = cnt + 1;
    }
    return false;
}

http_response_t DataService::_get(String path) {
    http_request_t request = _buildRequest(path);
    http_response_t response;

    logger.trace("GET %s://%s:%d%s", _scheme.c_str(), request.hostname.c_str(), request.port, request.path.c_str());

    String auth = String::format("Bearer %s", _bearerToken.c_str());

    http_header_t headers[] = {
        { "Accept", "application/json" },
        { "Authorization", auth },
        { NULL, NULL } // NOTE: Always terminate headers will NULL
    };
    http_client.get(request, response, headers);

    logger.trace("Response status: %d", response.status);
    logger.trace("Response Body: %s", response.body.c_str());

    return response;
}

http_response_t DataService::_post(String path, JsonDocument jDoc){
    http_request_t request = _buildRequest(path, jDoc);
    http_response_t response;

    logger.trace("POST %s://%s:%d%s", _scheme.c_str(), request.hostname.c_str(), request.port, request.path.c_str());
    logger.trace("Data: %s", request.body.c_str());

    String auth = String::format("Bearer %s", _bearerToken.c_str());

    http_header_t headers[] = {
        { "Content-Type", "application/json" },
        { "Accept", "application/json" },
        { "Authorization", auth },
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

http_request_t DataService::_buildRequest(String path, JsonDocument jDoc) {
    char data[1024];
    serializeJson(jDoc, data);
    http_request_t request = _buildRequest(path);
    request.body = data;
    return request;
}

JsonDocument DataService::_respToJson(http_response_t response) {
    JsonDocument doc;
    if (response.status == 200){
        DeserializationError error = deserializeJson(doc, response.body.c_str());
        if (error) {
            logger.error("deserializeJson() failed: ");
            // DO SOMETHING TO THROW AN ERROR 
        }
    }

    return doc;
}

device_data_t DataService::_parseDeviceData(JsonDocument jDoc) {
    device_data_t res = {true};
    if (!jDoc.isNull()) {
        res.isNull = false;
        JsonObject deviceDetails = jDoc.as<JsonObject>();
        res.id = String(deviceDetails["id"].as<const char*>());
        res.deviceType = String(deviceDetails["deviceType"].as<const char*>());       
        res.emptyKegWeight = deviceDetails["emptyKegWeightGrams"].as<float>(); 
    }
    return res;
}

void DataService::_generateBearerToken(String apiKey){
    String token = String::format("device|%s", apiKey.c_str());

    _bearerToken = Base64::encodeToString((const uint8_t *)token.c_str(), token.length());
    logger.trace("Bearer token %s", _bearerToken.c_str());
}
