#ifndef _KEG_VOL_MON_DATA_SVC_
#define _KEG_VOL_MON_DATA_SVC_

#include "Particle.h"
#include <ArduinoJson.h>
#include <HttpClient.h>

typedef struct {
    bool isNull;
    String id;
    String deviceType;
    float emptyKegWeight;
} device_data_t;

typedef struct {
    String id;
    float latestMeasurement;
    long latestMeasurementTS;
    int state;
    float emptyKegWeight;
} device_status_t;

class DataService 
{
    public:
        DataService(bool enabled, String deviceType, String hostname, int port, String apiKey, bool secure=false, int maxRetries=3);

        bool ping();
        device_data_t findDevice();
        device_data_t registerDevice();
        bool sendMeasurement(String id, float measurement, long timestamp);
        bool sendStatus(device_status_t status);

    private:
        bool _enabled;
        String _deviceType;
        String _hostname;
        int _port;
        String _scheme;
        int _maxRetries;
        String _bearerToken;
        http_request_t _buildRequest(String path);
        http_request_t _buildRequest(String path, JsonDocument jDoc);
        http_response_t _get(String path);
        http_response_t _post(String path, JsonDocument jDoc);
        JsonDocument _respToJson(http_response_t response);
        device_data_t _parseDeviceData(JsonDocument jDoc);
        void _generateBearerToken(String apiKey);
};

#endif