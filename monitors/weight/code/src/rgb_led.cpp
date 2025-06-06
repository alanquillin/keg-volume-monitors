#include "rgb_led.h"

int RGB_BLUE   = 0x0000FF;
int RGB_GREEN  = 0x00FF00;
int RGB_RED    = 0xFF0000;
int RGB_WHITE  = 0xFFFFFF;
int RGB_OFF    = 0x000000;
int RGB_ORANGE = 0xFF6000;

RGBLED::RGBLED(int redPin, int greenPin, int bluePin) {
    RED_PIN = redPin;
    GREEN_PIN = greenPin;
    BLUE_PIN = bluePin;
}

RGBLED::RGBLED() {
}

void RGBLED::begin() {
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    
    setColor(RGB_OFF);

    blinkTimer = new Timer (500, &RGBLED::blink, *this);
}

void RGBLED::begin(int redPin, int greenPin, int bluePin) {
    RED_PIN = redPin;
    GREEN_PIN = greenPin;
    BLUE_PIN = bluePin;
    begin();
}

void RGBLED::setColor(int rgb, bool store) {
    int r = ((rgb >> 16) & 0xFF);
    int g = ((rgb >> 8) & 0xFF);
    int b = ((rgb) & 0xFF);

    analogWrite(RED_PIN, r);
    analogWrite(GREEN_PIN,  g);
    analogWrite(BLUE_PIN, b);

    if (store) {
        CURRENT_COLOR = rgb;
    }
}

void RGBLED::blinkFast() {
    startBlink(100);
}

void RGBLED::blinkFast(int rgb, bool store) {
    setColor(rgb, store);
    blinkFast();
}

void RGBLED::blinkSlow() {
    startBlink(400);
}

void RGBLED::blinkSlow(int rgb, bool store) {
    setColor(rgb, store);
    blinkSlow();
}

void RGBLED::stopBlink() {
    if (blinkTimer->isActive()) {
        blinkTimer->stop();
        setColor(CURRENT_COLOR, false); //in case we stop it when it is off mid blink
    }
}

void RGBLED::startBlink(int period) {
    blinkTimer->changePeriod(period);
    if (!blinkTimer->isActive()) {
        blinkTimer->start();
    }
}

void RGBLED::blink() {
    if (BLINK_ON) {
        // turn LED off
        setColor(RGB_OFF, false);
    } else {
        // turn LED on
        setColor(CURRENT_COLOR, false);
    }
    BLINK_ON = !BLINK_ON;
}

int RGBLED::getCurrentColor() {
    return CURRENT_COLOR;
}