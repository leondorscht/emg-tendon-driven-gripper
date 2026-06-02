#include "config.h"
#include <Servo.h>
#include <math.h>

Servo servos[NUM_SERVOS];

// RMS buffer
int rms_buffer[RMS_WINDOW];
int rms_index = 0;
bool rms_filled = false;

// State detection
bool is_closed = false;
int activation_counter = 0;
int release_counter = 0;

void setup() {
  Serial.begin(SERIAL_BAUDRATE);

#if MODE_CALIBRATION
  setup_calibration();
#else
  setup_control();
#endif
}

void loop() {
#if MODE_CALIBRATION
  calibration_loop();
#else
  control_loop();
#endif
}

void setup_calibration() {
  // Analog input does not need setup
}

void setup_control() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(SERVO_PINS[i]);
  }
  set_all_servos(SERVO_CLOSE_ANGLE);

  delay(1000);

  set_all_servos(SERVO_OPEN_ANGLE);
}

void calibration_loop() {
  // During calibration we send RAW values.
  // Python calculates baseline and RMS threshold from these.
  int raw_value = analogRead(EMG_PIN);

  Serial.println(raw_value);

  delay(5);
}

void control_loop() {
  int emg_value = read_emg_rms();

  if (!is_closed) {
    if (emg_value > EMG_THRESHOLD) {
      activation_counter++;
    } else {
      activation_counter = 0;
    }

    if (activation_counter >= ACTIVATION_COUNT_THRESHOLD) {
      is_closed = true;
      set_all_servos(SERVO_CLOSE_ANGLE);
      activation_counter = 0;
      release_counter = 0;
    }
  } else {
    if (emg_value < EMG_THRESHOLD) {
      release_counter++;
    } else {
      release_counter = 0;
    }

    if (release_counter >= RELEASE_COUNT_THRESHOLD) {
      is_closed = false;
      set_all_servos(SERVO_OPEN_ANGLE);
      release_counter = 0;
      activation_counter = 0;
    }
  }

  Serial.println(emg_value);

  delay(5);
}

void set_all_servos(int servo_angle) {
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].write(servo_angle);
  }
}

int read_emg_rms() {
  int raw = analogRead(EMG_PIN);

  int centered = raw - EMG_BASELINE;

  rms_buffer[rms_index] = centered;
  rms_index++;

  if (rms_index >= RMS_WINDOW) {
    rms_index = 0;
    rms_filled = true;
  }

  int count = rms_filled ? RMS_WINDOW : rms_index;

  if (count == 0) {
    return 0;
  }

  long sum_sq = 0;

  for (int i = 0; i < count; i++) {
    long v = rms_buffer[i];
    sum_sq += v * v;
  }

  float mean_sq = (float)sum_sq / count;

  return (int)sqrt(mean_sq);
}