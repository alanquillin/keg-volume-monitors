#ifndef KEG_VOL_MON_WEIGHT_CONFIG
#define KEG_VOL_MON_WEIGHT_CONFIG

#include "Particle.h"

#if (PLATFORM_ID == PLATFORM_PHOTON)
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
    const int BTN_PIN = D6;
    const int RED_PIN = D2;
    const int GREEN_PIN = D1;
    const int BLUE_PIN = D0;
#endif

#if (PLATFORM_ID == PLATFORM_P2)
    const int HX711_DOUT_PIN = D19;
    const int HX711_SCK_PIN = D18;
    const int BTN_PIN = A0;
    const int RED_PIN = D13;
    const int GREEN_PIN = D14;
    const int BLUE_PIN = D16;
#endif

#endif