#include "Particle.h"
#include "config.h"
#include <HX711ADC.h>
#include <math.h>
//#include "../../../shared-lib/rgb_led.h"
#include "rgb_led.h"
//#include "../../../shared-lib/service.h"
#include "service.h"

SYSTEM_MODE(SEMI_AUTOMATIC);
// Run Setup code immediately.  This is enabled by default in OS v6.2.0 and above
#if (SYSTEM_VERSION < SYSTEM_VERSION_DEFAULT(6, 2, 0))
SYSTEM_THREAD(ENABLED);
#endif

// declare function prototypes
bool sendStatus();
bool getSetDeviceData();

Timer statusUpdater(STATUS_UPDATE_PERIOD_MS, sendStatus);

SerialLogHandler logHandler(LOG_LEVEL_WARN, {
    { "app", LOG_LEVEL_TRACE }, // Default logging level for all app messages
    { "app.service", LOG_LEVEL_TRACE } // Logging level for data service
});

HX711ADC scale(HX711_DOUT_PIN, HX711_SCK_PIN);		// parameter "gain" is omitted; the default value 128 is used by the library
RGBLED led(RED_PIN, GREEN_PIN, BLUE_PIN);
DataService dataService(SERVICE_ENABLED, "weight", HOSTNAME, PORT, false);
device_data_t deviceData = {true};

float LAST_MEASUREMENT = 0;
time32_t LAST_MEASUREMENT_TS = 0;

bool BTN_PRESSED = false;
unsigned long BTN_PRESSED_ON;
bool CALIBRATION_MODE_ENABLED = false;
bool CALIBRATING = false;
bool TESTING_LEDS = false;
bool MAINTENANCE_MODE = false;

int _getState(bool doPing) {
    if (CALIBRATING) {
        return 11;
    }

    if (CALIBRATION_MODE_ENABLED) {
        return 10;
    }

    if (MAINTENANCE_MODE) {
        return 99;
    }

    if (doPing) {
        if (!dataService.ping()) {
            return 2;
        }
    }

    return 1;
}

void storeCalibrationScale(float cal) {
    EEPROM.put(0, cal);
}

float getCalibrationScale() {
    float cal;
    EEPROM.get(0, cal);
    return cal;
}

void storeCalibrationOffset(long offset) {
    EEPROM.put(4, offset);
}

long getCalibrationOffset() {
    long offset;
    EEPROM.get(4, offset);
    return offset;
}

bool sendStatus() {
    if (deviceData.isNull) {
        Log.trace("No device info currently set, attempting to retrieve before sending status");
        if(!getSetDeviceData()){
            Log.warn("No device info found from service.  Service may not be available ATM, skipping sendStatus.");
            return false;
        }
    }

    device_status_t status;
    status.id = deviceData.id;
    status.latestMeasurement = LAST_MEASUREMENT;
    status.latestMeasurementTS = LAST_MEASUREMENT_TS;
    
    status.state = _getState(false);
    return dataService.sendStatus(status);
}

void tare() {
    scale.power_up();
    scale.tare();
    scale.power_down();
    storeCalibrationOffset(scale.get_offset());
    Log.trace("Tare complete, offset stored: %li", scale.get_offset());
}

void initCalibration() {
    CALIBRATION_MODE_ENABLED = true;

    scale.set_scale();
    tare();
}

// Puts the scale in calibration mode and resets.  Assumes the scale is clear or has the inital tare weight on
/**
 * @brief CLOUD FUNCTION CALLBACK - Performs a tare function and stores the offset in memory
 * 
 * @param _ String: ignored and unused
 * @return int 
 */
int tareCld(String _ = "") {
    tare();
    return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Performs a tare function, resets the calibration scale and puts the device in calibration mode
 * 
 * @param _ String: ignored and unused
 * @return int 
 *      @error codes:
 *          -99 - Function succeeded but was unable to send the status update to the service
 */
int initCalibrationCld(String _ = "") {
    initCalibration();
    
    if (!sendStatus()) {
        return -99;
    }
    return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Cancels calibration mode and resets the previous calibration scale value
 * 
 * @param _ String: ignored and unused
 * @return int - A value of 1 is return to represent successfully cancellation of calibration mode
 *      @error codes:
 *          -1 - If the device is currently calibration
 *          -2 - If there is no previous calibration value found.
 *          -99 - Function succeeded but was unable to send the status update to the service
 */
int cancelCalibrationCld(String _ = "") {
    if (CALIBRATING) {
        return -1;
    }
    float cal = getCalibrationScale();
    float offset = getCalibrationOffset();
    
    if (isnan(cal) || isnan(offset)) {
        return -2;
    }
    
    //blinkLEDSlow.stop();
    scale.set_scale(cal);
    scale.set_offset(offset);
    
    CALIBRATION_MODE_ENABLED = false;
    if(!sendStatus()) {
        return -99;
    }
    return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Resets the local EEPROM and restarts the system.
 * 
 * @param _ String: ignored and unused
 * @return int 
 */

int cleanMemAndRestartCld(String _ = "") {
  EEPROM.clear();
  System.reset(2);
  return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Uses the provided known weight to calibrate the scale.  The weight unit is irrelevant 
 * and whatever weight you used will be used to provide wights with the same units.
 * 
 * Example:  You passed in the value of 4535.923 which represented the weight in gram, then the scale will provide units
 *           in grams.  So to get lbs, you would divide the value provided by the scale by 453.592.  
 * 
 * @param String:cal_weight_str - The string representing the known weight to use for calibration
 * @return int - A value of 1 is return to represent successful calibration, negative numbers return indicate an error
 *      @error codes:
 *          -1 - Unable to parse input value to float
 *          -99 - Function succeeded but was unable to send the status update to the service
 * 
 * 
 * TODO: 
 *      - Need to make this smarter and compare the sample iterations to try and identify if the weight have either
 *        been removed or changed while calibration was in progress
 */
 
int calibrateCld(String calWeight_s) {
    float calWeight = calWeight_s.toFloat();
    if (calWeight == 0 && calWeight_s != "0") {
        return -1;
    }

    if (calWeight < DEFAULT_EMPTY_KEG_W) {
        if (!ALLOW_LOW_WEIGHT_CALIBRATION) {
            Log.error("Calibration failed because the calibration weight was below %.2fg", DEFAULT_EMPTY_KEG_W);
            return -2;
        }

        Log.warn("Calibrating with weight lower %.2fg which is less than the empty keg weight: %.2f", calWeight, DEFAULT_EMPTY_KEG_W);
    }
    
    CALIBRATING = true;
    sendStatus();
    Log.info("Starting calibration.  Known calibration weight: %0.2f", calWeight);
    float units_t = 0;
    int cnt = 10;
    int sampleCnt = 10;
    scale.power_up();
    Log.trace("starting calibration sampling.  Total sample groups: %i", cnt);
    for(int i=0; i<cnt; i++) {
        float units = scale.get_units(sampleCnt);
        units_t = units_t + units;
        Log.trace("Sample group %i of %i.  Sample count = %i, average unit value: %.2f", i+1, cnt, sampleCnt, units);
        delay(500);
    }
    float cal = (units_t / cnt) / calWeight;
    Log.info("Calibration complete, calibration scale value: %0.2f", cal);
    scale.set_scale(cal);

    Log.trace("Testing calibration.  New sampple must be withing the differential threshold: %.2f", DIFF_THRESHOLD);
    float diff = calWeight * DIFF_THRESHOLD;
    float max = calWeight + diff;
    float min = calWeight - diff;
    float sample = scale.get_units(sampleCnt);

    if(sample < min || sample > max) {
        Log.error("Calibration failed, the new sample %.2f was out side of the allowed range: min: %.2f, max: %.2f", sample, min, max);
        scale.set_scale();  // reset calibration scale
        return -3;
    }
    
    storeCalibrationScale(cal);
    scale.power_down();
    CALIBRATION_MODE_ENABLED = false;
    CALIBRATING = false;
    if(!sendStatus()){
        return -99;
    }
    return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Runs a quick visual test of the RGB LED.  The LED will cycle once from 
 *      White->Red->Green->Blue for 2 seconds each.  
 * 
 * @param _ String: ignored and unused
 * @return int 
 */
int testLedsCld(String _ = "") {
    if (CALIBRATING || CALIBRATION_MODE_ENABLED) {
        Log.error("Cannot run LED test as calibration is in process.");
        return -1;
    }
    
    TESTING_LEDS = true;
    
    Log.info("Starting LED testing.");
    Log.info("Testing white");
    led.setColor(RGB_WHITE, false);
    delay(2000);
    Log.info("Testing red");
    led.setColor(RGB_RED, false);
    delay(2000);
    Log.info("Testing green");
    led.setColor(RGB_GREEN, false);
    delay(2000);
    Log.info("Testing blue");
    led.setColor(RGB_BLUE, false);
    delay(2000);
    Log.info("LED test complete");
    led.setColor(led.getCurrentColor());
    
    TESTING_LEDS = false;
    
    return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Sends the current device status to service
 * 
 * @param _ String: ignored and unused
 * @return int A value of 1 is return to represent successful data push
 *      @error codes:
 *          -1 - Failed to push the data to the data service
 *          -2 - The extended device information could not be retrieved from the data service
 *          -3 - No sample has been taken yet
 */
int sendStatusCld(String _ = "") {
    if (deviceData.isNull) {
        Log.info("Extended device data not found from data service, attempting to discover...");
        deviceData = dataService.findDevice();

        if (deviceData.isNull) {
            Log.error("discovery failed, no extended device data could be retrieved form the data service");
            return -2;
        }
    }

    if (LAST_MEASUREMENT_TS == 0) {
        return -3;
    }
    
    if (sendStatus()) {
        Log.info("Successfully saved the measurement with the Data Service");
        return 1;
    } else {
        Log.error("Failed to save the measurement with the Data Service");
        return -1;
    }
}
/**
 * @brief CLOUD FUNCTION CALLBACK - Puts device in maintenance mode
 * 
 * @param _ String: ignored and unused
 * @return int 
 *          -99 - Function succeeded but was unable to send the status update to the service
 */
int startMaintenanceModeCld(String _ = "") {
    if (CALIBRATING || CALIBRATION_MODE_ENABLED) {
        Log.error("Cannot enter maintenance mode while calibration is in process.");
        return -1;
    }

    Log.info("Entering maintenance mode.");
    MAINTENANCE_MODE = true;
    if(!sendStatus()){
        return -99;
    }
    return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Exits maintenance mode
 * 
 * @param _ String: ignored and unused
 * @return int 
 *          -99 - Function succeeded but was unable to send the status update to the service
 */
int stopMaintenanceModeCld(String _ = "") {
    if (CALIBRATING || CALIBRATION_MODE_ENABLED) {
        Log.error("Cannot exit maintenance mode while calibration is in process.");
        return -1;
    }

    Log.info("Exiting maintenance mode.");
    MAINTENANCE_MODE = false;
    if(!sendStatus()){
        return -99;
    }
    return 1;
}

/**
 * @brief CLOUD FUNCTION CALLBACK - Sends the last stored sample to the data service
 * 
 * @param _ String: ignored and unused
 * @return int Value representing this current state of the device
 *          1 - Normal function and data service available
 *          2 - Normal function but data service is not available
 *          10 - Calibration mode enabled
 *          11 - Calibration in progress
 *          99 - Maintenance mode
 */
int getStateCld(String _ = "") {
    return _getState(true);
}

bool getSetDeviceData() {
    bool res = dataService.ping();
    if (!res) {
        Log.error("Data service ping failed.");
        return false;
    } else {
        Log.info("Data service ping successful");
        deviceData = dataService.findDevice();
        if (deviceData.isNull) {
            Log.error("Device not found with Data Service.");
            deviceData = dataService.registerDevice();
            if (deviceData.isNull) {
                Log.error("Failed to register device with the Data Service");
                return false;
            }
        } else {
            Log.trace("Found or successfully registered device with the Data Service.  Id: %s", deviceData.id.c_str());
        }
    }
    return true;
}

void setup() {
    led.begin();
    led.setColor(RGB_WHITE);
    led.blinkFast();
    
    pinMode(BTN_PIN, INPUT_PULLDOWN);
    
    waitFor(Serial.isConnected, 10000);
    
    Log.info("Initiating startup sequence...");
    Log.trace("Attempting to connect to WiFi.");

    WiFi.on();
    WiFi.connect();
    
    if(waitFor(WiFi.ready, 10000)){
        Log.info("Successfully connected to WiFi.");
    } else {
        Log.error("Failed to connect to Wifi in time... this may go badly ");
    }

    scale.begin();
    scale.power_down();
    
    Particle.function("startCalibration", initCalibrationCld);
    Particle.function("cancelCalibration", cancelCalibrationCld);
    Particle.function("calibrate", calibrateCld);
    Particle.function("tare", tareCld);
    Particle.function("testLEDs", testLedsCld);
    Particle.function("clearMemory", cleanMemAndRestartCld);
    Particle.function("sendStatus", sendStatusCld);
    Particle.function("startMaintenanceMode", startMaintenanceModeCld);
    Particle.function("stopMaintenanceMode", stopMaintenanceModeCld);
    Particle.function("getState", getStateCld);
    
    Log.trace("Connecting to Particle Cloud");
    Particle.connect();
    if(waitFor(Particle.connected, 10000)) {
        Log.info("Successfully connected to Particle cloud");
    } else {
        Log.error("Failed to connect to Particle cloud");
    }

    getSetDeviceData();

    float cal = getCalibrationScale();
    long calOffset = getCalibrationOffset();
    Log.trace("Startup Calibration Value: %.2f, offset: %li", cal, calOffset);
    
    if (isnan(cal) || cal == 0.0 || isnan(calOffset) || calOffset == 0) {
        Log.info("No calibration set in memory, starting calibration mode.");
        initCalibration();	
    } else {
        scale.set_scale(cal);
        scale.set_offset(calOffset);
    }

    statusUpdater.start();
    sendStatus();
    led.stopBlink();

    Log.trace("Scale config: offset: %li, scale: %.2f", scale.get_offset(), scale.get_scale());
    Log.trace("Startup sequence complete!");
}

void loop() {
    int dVal = digitalRead(BTN_PIN);
    if (dVal == HIGH) {
        if (!BTN_PRESSED) {
            Log.info("External function switch press detected");
            BTN_PRESSED_ON = millis();
        }
        BTN_PRESSED = true;
    }

    if (BTN_PRESSED) {
        led.setColor(RGB_RED);
        unsigned long now = millis();
        unsigned long pressDuration = now - BTN_PRESSED_ON;
        bool doResetAction = false;
        if (pressDuration >= 5000) {
            led.blinkFast();
            doResetAction = true;
        }
        if (dVal != HIGH) {
            BTN_PRESSED = false;
            Log.info("External function switch pressed for %.2f seconds", pressDuration / 1000.0);
            if (doResetAction) {
                Log.info("Reset initiated by external function switch.");
                led.blinkSlow();
                delay(3000);
                System.reset(1);
            } 
        } else {
            delay(500);
        }
    } else if (TESTING_LEDS) {
        led.stopBlink();
        delay(1000);
    } else if (CALIBRATING) {
        led.setColor(RGB_BLUE);
        led.blinkFast();
        delay(500);
    } else if (CALIBRATION_MODE_ENABLED) {
        led.setColor(RGB_BLUE);
        led.blinkSlow();
        delay(1000);
    } else if (MAINTENANCE_MODE) {
        led.stopBlink();
        led.setColor(RGB_ORANGE);

        delay(1000);
    } else {
        led.stopBlink();
        // if moving from a different state, assume an empty keg and set to white.  
        if (led.getCurrentColor() != RGB_COLOR_WHITE && led.getCurrentColor() != RGB_COLOR_GREEN) {
            led.setColor(RGB_WHITE);
        }

        scale.power_up();
        float units = scale.get_units(10);
        scale.power_down(); // put the ADC in sleep mode
        
        // The sampling can take a second or 2, and in the mean time, cloud fucntions can change the state, this checks that before doing anything with the value.
        if (!BTN_PRESSED && !TESTING_LEDS && !CALIBRATING && !CALIBRATION_MODE_ENABLED && !MAINTENANCE_MODE) {
            Log.trace("Sample taken: %.2f", units);
                
            if (units < DEFAULT_EMPTY_KEG_W) {
                led.setColor(RGB_WHITE);
            } else {
                led.setColor(RGB_GREEN);
                float diff = units * DIFF_THRESHOLD;
                if (units > (LAST_MEASUREMENT + diff) || units < (LAST_MEASUREMENT - diff)) {
                    Log.info("New measurement found that exceeds the differential threshold.  Measurement value: %.2f", units);
                    Log.trace("Last measurement: %.2f, current measurements: %.2f, differential: %.2f, differential threshold: %.2f", LAST_MEASUREMENT, units, diff, DIFF_THRESHOLD);

                    LAST_MEASUREMENT = units;
                    LAST_MEASUREMENT_TS = Time.now();

                    if (deviceData.isNull) {
                        Log.info("Extended device data not found from data service, attempting to discover");
                        deviceData = dataService.findDevice();
                    }

                    if (deviceData.isNull) {
                        Log.warn("UNKNOWN id for the device from the device service...");
                    } else {
                        led.blinkFast();
                        if (dataService.sendMeasurement(deviceData.id, units, LAST_MEASUREMENT_TS)) {
                            Log.info("Successfully saved the measurement with the Data Service");
                        } else {
                            Log.error("Failed to save the measurement with the Data Service");
                        }
                        led.stopBlink();
                    }
                }
            }
        }

        delay(1000);
    }
  
}