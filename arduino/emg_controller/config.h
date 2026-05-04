#pragma once

// Operation Mode
// set the mode to either calibration (1) or control (0)
#define MODE_CALIBRATION 1

// Serial
#define SERIAL_BAUDRATE 9600

// Servos
#define NUM_SERVOS 3
const int SERVO_PINS[NUM_SERVOS] = {9, 10, 11};

#define SERVO_OPEN_ANGLE 0
#define SERVO_CLOSE_ANGLE 90

// EMG
#define EMG_PIN A0
#define EMG_THRESHOLD 400
#define EMG_SMOOTHING_WINDOW 10