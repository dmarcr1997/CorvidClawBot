#include "Arduino_RouterBridge.h"

// Pin definitions - update when DRV8833 arrives
#define AIN1 5
#define AIN2 6
#define BIN1 9
#define BIN2 10

void setup() {
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  
  Bridge.begin();
  Bridge.provide("move", move);
  Bridge.provide("turn", turn);
  Bridge.provide("stop", stop);
  Bridge.provide("wobble", wobble);
  Bridge.provide("get_sensor_reading", get_sensor_reading);
}

void loop() {
  // STM side is purely reactive - waits for RPC calls
}

void move(int speed, bool forward) {
  int pwm = map(speed, 0, 100, 0, 200);
  if (forward) {
    analogWrite(AIN1, pwm);
    digitalWrite(AIN2, LOW);
    analogWrite(BIN1, pwm);
    digitalWrite(BIN2, LOW);
  } else {
    digitalWrite(AIN1, LOW);
    analogWrite(AIN2, pwm);
    digitalWrite(BIN1, LOW);
    analogWrite(BIN2, pwm);
  }
}

void turn(int speed, bool left) {
  int pwm = map(speed, 0, 100, 0, 200);
  if (left) {
    digitalWrite(AIN1, LOW);
    analogWrite(AIN2, pwm);
    analogWrite(BIN1, pwm);
    digitalWrite(BIN2, LOW);
  } else {
    analogWrite(AIN1, pwm);
    digitalWrite(AIN2, LOW);
    digitalWrite(BIN1, LOW);
    analogWrite(BIN2, pwm);
  }
}

void stop() {
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
}

void wobble() {
  for(int i = 0; i < 3; i++) {
    turn(30, true);
    delay(150);
    turn(30, false);
    delay(150);
  }
  stop();
}

// Placeholder - expand when sensors are added
int get_sensor_reading() {
  return 0;
}