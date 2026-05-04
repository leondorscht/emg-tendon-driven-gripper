#include "config.h"
#include <Servo.h>

Servo servos[NUM_SERVOS];

int emg_buffer[EMG_SMOOTHING_WINDOW];
int emg_buffer_index = 0;
long emg_sum = 0;
bool emg_buffer_filled = false;

void setup() {
  Serial.begin(SERIAL_BAUDRATE);

#if MODE_CALIBRATION
  setup_calibration();
#else
  setup_control();
#endif
}

void loop() {
// decide on what loop to run based on the config
#if MODE_CALIBRATION
  calibration_loop();
#else
  control_loop();
#endif
}

void setup_calibration() {
  // set up of EMG pin not required (analog, serial already done)
}

void setup_control() {
  // set up of EMG pin not required (analog, serial already done)
  // set up servo pins
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(SERVO_PINS[i]);
  }

  set_all_servos(SERVO_OPEN_ANGLE);
}

void calibration_loop() {
  // records emg data and sends it over serial to python, which then selects
  // the threshold value for emg and runs the control loop

  int emg_value = read_smoothed_emg();

  Serial.println(emg_value);

  delay(5);
}

void control_loop() {
  // continously read emg data and compare to the threshold.
  // if emg > threshold, close the gripper
  int emg_value = read_smoothed_emg();

  if (emg_value > EMG_THRESHOLD) {
    set_all_servos(SERVO_CLOSE_ANGLE);
  } else {
    set_all_servos(SERVO_OPEN_ANGLE);
  }

  delay(10);
}

void set_all_servos(int servo_angle) {
  // set the angle for the servo
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].write(servo_angle);
  }
}

int read_smoothed_emg() {
  // read the raw value
  int raw_value = analogRead(EMG_PIN);

  // remove the old buffer value and replace it with new
  emg_sum -= emg_buffer[emg_buffer_index];
  emg_buffer[emg_buffer_index] = raw_value;
  emg_sum += raw_value;

  // increase buffer idx to next place
  emg_buffer_index++;

  // if index exceeds buffer space, set again to 0
  if (emg_buffer_index >= EMG_SMOOTHING_WINDOW) {
    emg_buffer_index = 0;
    emg_buffer_filled = true;
  }

  // if buffer filled, set count to EMG_SMOOTHING_WINDOW else emg_buffer_index
  // --> do not always divide vy EMG_SMOOTHING_WINDOW
  int count = emg_buffer_filled ? EMG_SMOOTHING_WINDOW : emg_buffer_index;

  // edge case
  if (count == 0) {
    return raw_value;
  }

  // mean
  return emg_sum / count;
}
