#include "Particle.h"
#include "config.h"
#include <HX711ADC.h>
#include <math.h>
#include "../../../shared-lib/rgb_led.h"

// Run Setup code immediately.  This is enabled by befault in OS v6.2.0 and above
#if (SYSTEM_VERSION < SYSTEM_VERSION_DEFAULT(6, 2, 0))
SYSTEM_THREAD(ENABLED);
#endif

SerialLogHandler logHandler(LOG_LEVEL_ALL);

HX711ADC scale(HX711_DOUT_PIN, HX711_SCK_PIN);		// parameter "gain" is omitted; the default value 128 is used by the library
RGBLED led(RED_PIN, GREEN_PIN, BLUE_PIN);

bool BTN_PRESSED = false;
unsigned long BTN_PRESSED_ON;
bool CALIBRATION_MODE_ENABLED = false;
bool CALIBRATING = false;
bool TESTING_LEDS = false;

void store_calibration(float cal) {
    EEPROM.put(0, cal);
}

float get_calibration() {
    float cal;
    EEPROM.get(0, cal);
    return cal;
}

int tare(String _ = "") {
    scale.power_up();
    scale.tare();
    scale.power_down();
    
    return 1;
}

// Puts the scale in calibration mode and resets.  Assumes the scale is clear or has the inital tare weight on
int init_calibration(String _ = "") {
    CALIBRATION_MODE_ENABLED = true;
    scale.set_scale();
    tare();
    
    return 1;
}

int cancel_calibration(String _ = "") {
    if (CALIBRATING) {
        return -1;
    }
    float cal = get_calibration();
    
    if (isnan(cal)) {
        return -2;
    }
    
    //blinkLEDSlow.stop();
    scale.set_scale(cal);
    
    CALIBRATION_MODE_ENABLED = false;
    return 1;
}

int cleanMemAndRestart(String _ = "") {
  EEPROM.clear();
  System.reset(2);
  return 1;
}

/**
 * CLOUD FUNCTION CALLBACK - Uses the provided known weight to calibrate the scale.  The weight unit is irrelevant 
 * and whatever weight you used will be used to provide wights with the same units.
 * 
 * Example:  You passed in the value of 4535.923 which represented the weight in gram, then the scale will provide units
 *           in grams.  So to get lbs, you would divide the value provided by the scale by 453.592.  
 * 
 * @param String:cal_weight_str - The string representing the known weight to use for calibration
 * @return int - A value of 1 is return to represent successful calibration, negative numbers return indicate an error
 *      @error codes:
 *          -1 - Unable to parse input value to float
 * 
 * 
 * TODO: 
 *      - Need to make this smarter and compare the sample iterations to try and identify if the weight have either
 *        been removed or changed while calibration was in progress
 */
 
int calibrate(String cal_weight_str) {
    float cal_weight = cal_weight_str.toFloat();
    if (cal_weight == 0 && cal_weight_str != "0") {
        return -1;
    }
    
    CALIBRATING = true;
    Log.info("Starting calibration.  Known calibration weight: %0.2f", cal_weight);
    float units_t = 0;
    int cnt = 20;
    scale.power_up();
    Log.trace("starting calibration sampling.  Total sample groups: %i", cnt);
    for(int i=0; i<cnt; i++) {
        int sampleCnt = 10;
        float units = scale.get_units(sampleCnt);
        units_t = units_t + units;
        Log.trace("Sample group %i of %i.  Sample count = %i, average unit value: %.2f", i+1, cnt, sampleCnt, units);
        delay(500);
    }
    float cal = (units_t / cnt) / cal_weight;
    Log.info("Calibration complete, calibration value: %0.2f", cal);
    store_calibration(cal);
    scale.set_scale(cal);
    scale.power_down();
    CALIBRATION_MODE_ENABLED = false;
    CALIBRATING = false;
    return 1;
}

int test_leds(String _ = "") {
    if (CALIBRATING || CALIBRATION_MODE_ENABLED) {
        Log.error("Cannot run LED test as calibration is in process.");
        return -1;
    }
    
    TESTING_LEDS = true;
    
    Log.info("Starting LED testing.");
    Log.info("Testing white");
    led.setColor(RGB_WHITE, false);
    delay(1000);
    Log.info("Testing red");
    led.setColor(RGB_RED, false);
    delay(1000);
    Log.info("Testing green");
    led.setColor(RGB_GREEN, false);
    delay(1000);
    Log.info("Testing blue");
    led.setColor(RGB_BLUE, false);
    delay(1000);
    Log.info("LED test complete");
    led.setColor(led.getCurrentColor());
    
    TESTING_LEDS = false;
    
    return 1;
}

int setLogLevel(String logLevel) {
    return 1;
}

void setup() {
    //Serial.begin(38400);

    pinMode(BTN_PIN, INPUT_PULLDOWN);
    
    led.begin();
    led.setColor(RGB_WHITE);
    led.blinkFast();
    delay(5000); // wait 5 seconds so the serial monitor can connect... dumb hack, I know ;P 
    
    scale.begin();
    scale.power_down();
    
    Log.trace("Config: offset: %ld, scale: %.2f", scale.get_offset(), scale.get_scale());
    
    if (!Particle.connected()) {
        Log.warn("Waiting to connect to particle cloud");
        int cnt = 0;
        while(!Particle.connected()) {
            cnt++;
            if (cnt > 10) {
                break;
            }
            delay(1000);
        }
    }
    
    Particle.function("startCalibration", init_calibration);
    Particle.function("cancelCalibration", cancel_calibration);
    Particle.function("calibrate", calibrate);
    Particle.function("tare", tare);
    Particle.function("testLEDs", test_leds);
    Particle.function("clearMemory", cleanMemAndRestart);
    Particle.function("setLogLevel", setLogLevel);
    
    float cal = get_calibration();
    Log.info("Startup Calibration Value: %.2f", cal);
    
    led.stopBlink();
    led.setColor(RGB_BLUE);
    
    if (isnan(cal) || cal == 0) {
        Log.info("No calibration set in memory, starting calibration mode.");
        init_calibration();	
    }
    
    Log.trace("Setup Complete!");
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
    } else {
        led.stopBlink();
        
        led.setColor(RGB_GREEN);
        scale.power_up();
        
        float units = scale.get_units(10);
        Log.trace("Sample taken: %.2f", units);
        
        scale.power_down();			        // put the ADC in sleep mode
        delay(1000);
    }
  
}