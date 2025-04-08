#ifndef _KEG_VOL_MON_DATA_SVC_
#define _KEG_VOL_MON_DATA_SVC_

#include <ArduinoJson.h>
#include <HttpClient.h>

const int DS_MAX_RETRY = 2;

typedef struct {
    bool isNull;
    String id;
    String manufacturerId;
    String deviceType;
} device_data_t;

class DataService {
public:
    DataService(bool enabled, String manufacturer, String manufacturerId, String deviceType, int port, String hostname = "", String ipAddress = "", bool secure=false);    
    DataService();
        
    void begin(bool enabled, String manufacturer, String manufacturerId, String deviceType, int port, String hostname = "", String ipAddress = "", bool secure=false);
    void begin();


    bool ping();
    device_data_t findDevice(String manufacturerId);
    device_data_t getDeviceData(String id);
    device_data_t registerDevice(String manufacturerId);
    bool sendMeasurement(String id, float measurement, long timestamp, uint8_t size);

private:
    bool _enabled;
    String _manufacturer;
    String _manufacturerId;
    String _deviceType;
    String _hostname;
    String _ipAddress;
    int _port;
    String _schema;
    http_request_t _buildRequest(String path);
    http_request_t _buildRequest(String path, JsonDocument jDoc, const uint16_t docSize=1024);
    JsonDocument _getJson(String path, const uint16_t docSize=1024);
    http_response_t _get(String path);
    http_response_t _get(http_request_t request);
    http_response_t _post(String path, JsonDocument jDoc, const uint16_t docSize=1024);
    http_response_t _post(http_request_t request);
    JsonDocument _respToJson(http_response_t response, const uint16_t docSize=1024);
    device_data_t _parseDeviceData(JsonDocument jDoc);
};

#endif