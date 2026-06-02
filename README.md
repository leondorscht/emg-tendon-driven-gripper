# EMG Tendon-Driven Gripper

Tendon-driven robotic gripper with EMG-based open/close control. An automated Python pipeline handles calibration, threshold computation, and Arduino firmware flashing — no manual configuration needed.

---

## System Overview

![Assembly View](images/Gripper_Assembly.png)

*Figure 1 – Servo-based gripper assembly.*

![Section View](images/Gripper_Section_Analysis.png)

*Figure 2 – Section view highlighting internal structure, bearings and actuator integration.*

---

## Design Reference

The mechanical concept of the gripper is inspired by the tendon-driven underactuated gripper presented in:

Yi, J., Kim, B., Cho, K.-J., & Park, Y.-L. (2023).  
**Underactuated Robotic Gripper With Fiber-Optic Force Sensing Tendons.**  
IEEE Robotics and Automation Letters, 8(11), 7607–7614.  
https://doi.org/10.1109/LRA.2023.3315204

This project is **not a direct reproduction** of the original system.  
Instead, the CAD model adapts key mechanical ideas from the paper into a simplified prototype intended for rapid prototyping with 3D printing, servo-based actuation, and EMG-based control.

---

## Repository Structure

```
emg-tendon-driven-gripper/
├── arduino/
│   └── emg_controller/
│       ├── emg_controller.ino   # Arduino sketch (calibration + control modes)
│       └── config.h             # Auto-generated hardware config (do not edit manually)
├── cad/
│   ├── gripper_v1_(legacy)/     # V1 cycloidal drive concept (STEP)
│   └── gripper_v2/              # V2 servo-based design (STEP, 3MF, STL)
├── data/
│   └── calibration.csv          # EMG calibration recording output
├── images/
├── python/
│   ├── run_pipeline.py          # End-to-end pipeline entry point
│   ├── calibration_recorder.py  # EMG serial reader, protocol generator, CSV recorder
│   ├── threshold_calculator.py  # RMS-based threshold from calibration data
│   ├── config_writer.py         # Writes arduino/emg_controller/config.h
│   └── arduino_flasher.py       # Compiles and uploads via arduino-cli
└── requirements.txt
```

---

## Signal Processing

EMG control relies on two steps: baseline removal and RMS feature extraction.

**Baseline removal** – during calibration, the median of all rest-state samples is computed and stored as `EMG_BASELINE`. In control mode, the Arduino subtracts this value from each raw ADC reading before computing RMS, removing the DC offset introduced by the sensor circuit (~340 ADC on the DFRobot Gravity EMG sensor).

**RMS (Root Mean Square)** – the signal energy over a sliding window of `RMS_WINDOW` centered samples is computed as:

```
RMS = sqrt( mean( (x - baseline)^2 ) )
```

RMS is more robust than a simple mean threshold because mean values are almost identical between rest and contraction states (both dominated by the DC offset), while RMS captures the increase in signal variance during muscle activation.

**Threshold** – computed from rest-state RMS values as:

```
threshold = rest_RMS_mean + multiplier × rest_RMS_std
```

With the default `multiplier = 2.0`, approximately 97.7% of rest-state RMS values fall below the threshold. A sanity check warns if the computed threshold exceeds the active-state RMS mean, indicating a failed calibration.

**State detection** – to avoid false triggers from transient spikes, the control loop requires the RMS to exceed the threshold for `ACTIVATION_COUNT_THRESHOLD` consecutive samples before closing, and to fall below it for `RELEASE_COUNT_THRESHOLD` consecutive samples before opening.

---

## Software Pipeline

The Python pipeline in `python/run_pipeline.py` automates the full calibration-to-control workflow:

1. **Write calibration config** – generates `config.h` with `MODE_CALIBRATION=1` and a passthrough threshold
2. **Flash calibration firmware** – compiles and uploads the sketch via `arduino-cli`
3. **Record calibration data** – guides the user through a rest/active protocol and records raw EMG values to CSV
4. **Compute threshold and baseline** – calculates `EMG_BASELINE` (median of rest values) and `EMG_THRESHOLD` (rest RMS mean + multiplier × rest RMS std) from the recorded data
5. **Write control config** – regenerates `config.h` with `MODE_CALIBRATION=0`, the computed threshold, and the baseline
6. **Flash control firmware** – uploads the final sketch; the Arduino now runs RMS-based EMG threshold control

### Arduino firmware modes

The sketch switches behaviour at compile time via `MODE_CALIBRATION` in `config.h`:

- **Calibration mode** – streams raw ADC values over serial at ~200 Hz; Python handles all signal processing
- **Control mode** – computes RMS on-device after baseline subtraction, closes all servos when `rms_value > EMG_THRESHOLD` for `ACTIVATION_COUNT_THRESHOLD` consecutive samples, opens them after `RELEASE_COUNT_THRESHOLD` consecutive samples below threshold

### Running the pipeline

```bash
pip install -r requirements.txt

cd python
python run_pipeline.py \
  --port /dev/ttyUSB0 \
  --fqbn arduino:avr:nano
```

Key arguments (all have defaults):

| Argument | Default | Description |
|---|---|---|
| `--port` | *(required)* | Serial port of the Arduino |
| `--fqbn` | *(required)* | Fully Qualified Board Name for arduino-cli |
| `--servo-pins` | `9 10 11` | PWM pins for servos |
| `--servo-open-angle` | `0` | Servo angle for open state |
| `--servo-close-angle` | `180` | Servo angle for closed state |
| `--rms-window` | `32` | RMS window size in samples |
| `--activation-count-threshold` | `20` | Consecutive samples above threshold to close |
| `--release-count-threshold` | `10` | Consecutive samples below threshold to open |
| `--state-length` | `5` | Seconds per active state during calibration |
| `--rest-length` | `5` | Seconds per rest state during calibration |
| `--num-repetitions` | `5` | Number of rest/active repetitions |
| `--threshold-multiplier` | `2.0` | Multiplier on rest RMS std for threshold |

`arduino-cli` must be installed and the target board core installed (`arduino-cli core install arduino:avr` for Nano/Uno).

---

## Actuation Iterations

### V1 – Cycloidal Transmission (Legacy)
- Multi-part cycloidal drive (~30 components)
- Concept validated mechanically
- Discontinued due to speed limitations and system complexity

### V2 – Servo-Based Actuation (Current)
- Direct MG90S servo integration
- Reduced mechanical complexity
- Improved responsiveness and controllability

The current prototype uses MG90S micro servos. They were intentionally selected for the initial prototype due to their low cost, availability, and ease of integration. Future iterations may explore higher-torque servos once the mechanical design and control pipeline are fully validated.

---

## Bill of Materials (Servo Version)

- 3× MG90S Micro Servo
- 9× MR128 ZZ Ball Bearings (8×12×3.5 mm)
- Nylon monofilament line (tendon)
- M3 and M4 fasteners
- Arduino Nano (or compatible)
- EMG sensor module with analog output (e.g. DFRobot Gravity EMG Sensor)

---

## Notes on Development

The mechanical design, hardware integration, signal processing approach, and software architecture were developed independently. AI assistance (Claude) was used selectively for code refactoring and documentation only.

---

## Design Files

The mechanical design was developed in Fusion 360. STEP and 3MF files are in `cad/gripper_v2/`. STL files for printing are in `cad/gripper_v2/stl_files/`.