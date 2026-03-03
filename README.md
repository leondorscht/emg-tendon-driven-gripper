# EMG Tendon-Driven Gripper

Tendon-driven robotic gripper prototype with servo-based actuation, designed for future EMG integration.

---

## System Overview

![Assembly View](images/Gripper_Assembly.png)

*Figure 1 – Current servo-based gripper assembly.*

![Section View](images/Gripper_Section_Analysis.png)

*Figure 2 – Section view highlighting internal structure, bearings and actuator integration.*

---

## Current Status

- Modular finger design completed  
- Servo-based actuation base implemented  
- Cycloidal transmission concept developed and discontinued  
- Assembly exported as STEP file  

This repository currently contains the CAD assembly (STEP format) for documentation and structural reference.  
STL files and manufacturing assets will be added in subsequent updates.

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

---

## Bill of Materials (Servo Version)

- 1× MG90S Micro Servo  
- 9× MR128 ZZ Ball Bearings (8×12×3.5 mm)  
- Nylon monofilament line (tendon)  
- M3 and M4 fasteners  

---

## Planned Next Steps

- Upload STL files for 3D printing  
- Embedded control integration  
- EMG signal acquisition  
- Signal preprocessing and closed-loop testing  

---

## Note

The mechanical design was developed in Fusion 360.  
The repository currently provides a neutral CAD export (STEP format).  
Design files and manufacturing documentation will be structured and added progressively.