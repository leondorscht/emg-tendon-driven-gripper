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
│   ├── threshold_calculator.py  # Statistical threshold from calibration data
│   ├── config_writer.py         # Writes arduino/emg_controller/config.h
│   └── arduino_flasher.py       # Compiles and uploads via arduino-cli
└── requirements.txt
```

---

## Software Pipeline

The Python pipeline in `python/run_pipeline.py` automates the full calibration-to-control workflow:

1. **Write calibration config** – generates `config.h` with `MODE_CALIBRATION=1` and a passthrough threshold
2. **Flash calibration firmware** – compiles and uploads the sketch via `arduino-cli`
3. **Record calibration data** – guides the user through a rest/active protocol and records smoothed EMG values to CSV
4. **Compute threshold** – calculates `rest_mean + multiplier × rest_std` from the recorded data
5. **Write control config** – regenerates `config.h` with `MODE_CALIBRATION=0` and the computed threshold
6. **Flash control firmware** – uploads the final sketch; the Arduino now runs EMG-threshold control

### Arduino firmware modes

The sketch switches behaviour at compile time via `MODE_CALIBRATION` in `config.h`:

- **Calibration mode** – streams smoothed EMG values over serial at 200 Hz
- **Control mode** – closes all servos when `emg_value > EMG_THRESHOLD`, opens them otherwise

EMG smoothing uses a rolling mean over a configurable window (`EMG_SMOOTHING_WINDOW`).

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
| `--servo-close-angle` | `90` | Servo angle for closed state |
| `--smoothing-window` | `10` | Rolling mean window for EMG |
| `--state-length` | `5` | Seconds per active state during calibration |
| `--rest-length` | `5` | Seconds per rest state during calibration |
| `--num-repetitions` | `5` | Number of rest/active repetitions |
| `--threshold-multiplier` | `3.0` | Multiplier on rest std for threshold |

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

- 1× MG90S Micro Servo (×3 for full three-finger configuration)
- 9× MR128 ZZ Ball Bearings (8×12×3.5 mm)
- Nylon monofilament line (tendon)
- M3 and M4 fasteners
- Arduino Nano (or compatible)
- EMG sensor module (e.g. MyoWare or equivalent analog output)

---

## Design Files

The mechanical design was developed in Fusion 360. STEP and 3MF files are in `cad/gripper_v2/`. STL files for printing are in `cad/gripper_v2/stl_files/`.
