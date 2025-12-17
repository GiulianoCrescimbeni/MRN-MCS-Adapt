# MCS Adaptation xApp for O-RAN

This repository contains the implementation of an **O-RAN xApp** designed to dynamically adapt the **Modulation and Coding Scheme (MCS)** of User Equipment (UEs) based on channel conditions (Bit Error Rate).

Developed as part of the **Mobile Radio Networks (2025)** course project, this xApp runs on the Near-RT RIC (RAN Intelligent Controller) and interacts with a **5G gNB (Next Generation NodeB) and its 5G antennas** via the **E2 Interface**.
## 📋 Project Overview

In O-RAN architectures, xApps are microservices that perform data collection and control on the Radio Access Network (RAN) in near-real-time. 

**The goal of this xApp is to:**
1.  **Monitor**: Periodically fetch telemetry data from the gNB (specifically Downlink BER and current MCS) for all connected UEs.
2.  **Analyze**: Compare the reported Bit Error Rate (BER) against a user-defined threshold.
3.  **Control**: 
    * If **BER > Threshold**: Force a robust (lower) MCS to improve signal reliability.
    * If **BER ≤ Threshold**: Restore the UE's original MCS to maximize throughput.

### Key Features
* **Custom E2SM Protocol**: Implements a custom E2 Service Model using Protocol Buffers to exchange `UE_LIST`, `ber_dl`, and `mcs_dl`.
* **Stateful Logic**: The xApp remembers the original MCS of a UE before overriding it, ensuring network restoration when channel conditions improve.
* **Interactive Configuration**: Thresholds and target MCS values are configurable at runtime.

---

## 🏗 Architecture

### Protocol Design (Protobuf)
The standard E2SM was extended to support specific telemetry fields:
* **Indication**: Returns a list of UEs with `RNTI`, `BER_DL`, and `MCS_DL`.
* **Control**: Accepts a list of UEs with `RNTI` and the new `MCS_DL` to apply.

---

## 📂 Repository Structure

```text

MCSAdapt-xApp.py        # Main Python xApp logic
gnb_message_handlers.c  # C extension for the gNB emulator to handle specific messages
ran_messages.proto      # Protocol Buffer definitions
ProtocolDesign.pdf      # Detailed documentation of the protocol design
README.md               # Project documentation
```
## Deployment

### 1. Environment Setup

**Prerequisites**
- Docker & Docker Compose: To run the RIC platform and containers.
- Python 3: For the xApp logic.
- ANTLab RIC Platform: This project relies on the specific O-RAN environment provided by ANTLab (Politecnico di Milano).

First, clone the base RIC composer repository to set up the O-RAN clusters and containers.

```bash
git clone [https://github.com/ANTLab-polimi/ric-composer.git](https://github.com/ANTLab-polimi/ric-composer.git)
cd ric-composer
docker-compose up
```

### 2. Configure the gNB Emulator
Replace the standard gnb_message_handlers.c in the gNB container with the version provided in this repo.
Recompile/Build the emulator inside the container:
```bash
# Inside the gNB container
docker exec -it gnb bash
cd /path/to/source
./build/gnb_e2server_emu
```
### 3. Start the E2 Agent
In a separate terminal, start the E2 agent:
```bash
docker exec -it gnb bash
cd ../ocp-e2sim
./run_e2sim.sh
```
### 4. Run the xApp
```bash
docker exec -it xapp /bin/sh
python3 MCSAdapt-xApp.py
```
