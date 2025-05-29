#ifndef _KEG_VOL_MON_RGB_LED_
#define _KEG_VOL_MON_RGB_LED_

#include "Particle.h"

extern int RGB_BLUE;
extern int RGB_GREEN;
extern int RGB_RED;
extern int RGB_WHITE;
extern int RGB_OFF;
extern int RGB_ORANGE;

class RGBLED 
{
    public:
        RGBLED(int redPin, int greenPin, int bluePin);    
        RGBLED();
        
        void begin(int redPin, int greenPin, int bluePin);
        void begin();

        void setColor(int rgb, bool store=true);
        void blinkFast();
        void blinkFast(int rgb, bool store=true);
        void blinkSlow();
        void blinkSlow(int rgb, bool store=true);
        void stopBlink();
        int getCurrentColor();
    
    private:
        Timer* blinkTimer;
        int RED_PIN;
        int GREEN_PIN;
        int BLUE_PIN;
        int CURRENT_COLOR;
        bool BLINK_ON;

        void blink();
        void startBlink(int speed);
};

#endif