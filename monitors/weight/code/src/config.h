#ifndef _KEG_VOL_MON_WEIGHT_CONFIG_
#define _KEG_VOL_MON_WEIGHT_CONFIG_

#include "Particle.h"

#if (PLATFORM_ID == PLATFORM_PHOTON || PLATFORM_ID == PLATFORM_PHOTON_PRODUCTION)
    /*******************************
    Photon - prototype
    *******************************/
    // const int HX711_DOUT_PIN = D5;
    // const int HX711_SCK_PIN = D4;
    // const int BTN_PIN = D6;
    // const int RED_PIN = D3;
    // const int GREEN_PIN = D2;
    // const int BLUE_PIN = D1;

    const int HX711_DOUT_PIN = A1;
    const int HX711_SCK_PIN = A0;
    const int BTN_PIN = A7;
    const int RED_PIN = D2;
    const int GREEN_PIN = D1;
    const int BLUE_PIN = D0;

    const String CHIP_MODEL = "Photon";
#endif

#if (PLATFORM_ID == PLATFORM_P2)
    const int HX711_DOUT_PIN = D19;
    const int HX711_SCK_PIN = D18;
    const int BTN_PIN = A0;
    const int RED_PIN = D13;
    const int GREEN_PIN = D14;  
    const int BLUE_PIN = D16;

    const String CHIP_MODEL = "Photon2 / P2";
#endif

const String HOSTNAME = "192.168.1.2";
const int PORT = 8001;
const bool SERVICE_ENABLED = true;
const String API_KEY = "SET API KEY HERE";

const float DIFF_THRESHOLD = .01;

/** Most standard stainless steal corny keg are a little over 4 Kg.  
 * Most standard stainless steal corny keg are a little over 4 Kg.  
 * This assumes calibration was done in g, if another unit was used then
 * Update this to the min weight you want as your threshold */ 
const float DEFAULT_EMPTY_KEG_W = 4000.0;
/** if false, calibration will fail if the calibration weight provided is 
 * less than DEFAULT_EMPTY_KEG_W */ 
const bool ALLOW_LOW_WEIGHT_CALIBRATION = true;

const int STATUS_UPDATE_PERIOD_MS = 600000;
const int WIFI_MON_PERIOD_MS = 120000;

#endif