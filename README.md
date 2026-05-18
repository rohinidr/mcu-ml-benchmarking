# MCU ML Benchmark

Benchmarking classification model inference across three microcontrollers for research purposes.

| Board | MCU | Framework |
|-------|-----|-----------|
| STM32N6570-DK | STM32N657 (Cortex-M55, Neural-ART NPU) | ST Edge AI + CMake |
| ESP32-S3 DevKit | ESP32-S3 (Xtensa LX7, vector extensions) | ESP-IDF + TFLite Micro |
| Arduino Nano 33 BLE Sense | nRF52840 (Cortex-M4F) | Arduino CLI + TFLite Micro |

Metrics collected per board: **inference time (µs)**, **accuracy**, **min/max latency**.

> **Note:** STM32N6570-DK results use the **Cortex-M55 CPU**, not the Neural-ART NPU. See [Known Limitations](#known-limitations).

---

## Table of Contents

- [Repository Structure](#repository-structure)
- [Development Container](#development-container)
- [Workflow Overview](#workflow-overview)
- [Step 1 — Train the Model](#step-1--train-the-model)
- [Step 2 — Convert and Export](#step-2--convert-and-export)
- [Step 3 — Build and Flash](#step-3--build-and-flash)
  - [STM32N6570-DK](#stm32n6570-dk)
  - [ESP32-S3](#esp32-s3)
  - [Arduino Nano 33 BLE Sense](#arduino-nano-33-ble-sense)
- [Collecting Results](#collecting-results)
- [Common Interface](#common-interface)
- [Known Limitations](#known-limitations)

---

## Repository Structure

```
mcu-ml-benchmark/
├── .devcontainer/
│   ├── devcontainer.json       # Single container with all three toolchains
│   └── setup.sh                # Installs arm-gcc, ESP-IDF, Arduino CLI, Python
├── firmware/
│   ├── common/
│   │   ├── model_interface.h   # Shared inference API — same across all boards
│   │   └── benchmark.h         # Shared timing and accuracy structs
│   ├── stm32n6/                # STM32N6570-DK target
│   │   ├── CMakeLists.txt
│   │   ├── memory.x
│   │   ├── include/
│   │   │   └── model_config.h  # Quantization params — update after conversion
│   │   └── src/
│   │       ├── main.c
│   │       ├── model_runner.c  # ST Edge AI runtime wrapper
│   │       └── platform.c      # SysTick timer, printf via UART/RTT
│   ├── esp32/                  # ESP32-S3 target
│   │   ├── CMakeLists.txt
│   │   ├── sdkconfig.defaults
│   │   └── main/
│   │       ├── CMakeLists.txt
│   │       ├── main.c
│   │       └── model_runner.c  # TFLite Micro wrapper
│   └── arduino/                # Arduino Nano 33 BLE Sense target
│       └── nano33_classifier/
│           ├── nano33_classifier.ino
│           ├── model_runner.cpp
│           ├── model_runner.h
│           └── model_config.h
├── model/
│   ├── train.py                # Train Keras classification model
│   ├── convert.py              # Convert to int8 TFLite + generate C headers
│   └── requirements.txt
├── results/
│   └── analysis.ipynb          # Paper figures and tables
└── .gitignore
```

---

## Development Container

The devcontainer installs all three toolchains in one container:

| Tool | Purpose |
|------|---------|
| `arm-none-eabi-gcc` | STM32N6 C cross-compiler |
| `cmake` + `ninja` | STM32N6 build system |
| ESP-IDF v5.3 | ESP32-S3 toolchain |
| Arduino CLI | Nano 33 BLE Sense build + flash |
| Python 3.11 + TensorFlow | Model training and conversion |
| `probe-rs` | STM32N6 flash via ST-LINK v3 |

**Host requirements** (bind-mounted into container):

| Host path | Purpose |
|-----------|---------|
| `~/STMicroelectronics/STM32Cube/STM32CubeProgrammer` | STM32CubeProgrammer CLI |
| `~/st/stm32cubeide_2.1.0/.../tools/bin` | STM32 signing tool |

### Open in Devcontainer

1. Install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.
2. Open this folder in VS Code.
3. Click **Reopen in Container** when prompted.
4. Wait for `setup.sh` to complete (~10–15 minutes on first run).

---

## Workflow Overview

```
train.py          →  saved_model/
                          │
convert.py        →  model.tflite  +  model_data.h  +  test_vectors.h
                                            │
                              copied into firmware/<target>/
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
              STM32N6                   ESP32-S3            Arduino Nano 33
           cmake + ninja              idf.py build        arduino-cli compile
           probe-rs flash             idf.py flash        arduino-cli upload
                    │                       │                       │
                    └───────────────────────┴───────────────────────┘
                                            │
                                   Serial output (CSV)
                                            │
                                   results/analysis.ipynb
```

---

## Step 1 — Train the Model

```bash
cd model
pip install -r requirements.txt
python train.py --dataset mnist --epochs 10 --output saved_model/
```

Replace `mnist` with `cifar10` or point `--output` to your own SavedModel directory.

---

## Step 2 — Convert and Export

Convert to int8 TFLite and generate C headers for all three targets in one command:

```bash
python convert.py \
    --model saved_model/ \
    --dataset mnist \
    --export-c-array \
    --export-test-vectors 100 \
    --output-dir ..
```

This generates:
- `firmware/<target>/model_data.h` — model weights as C array
- `firmware/<target>/src/test_vectors.h` — 100 quantized test samples + labels

It also prints the quantization parameters — copy them into each `model_config.h`:

```c
// firmware/<target>/include/model_config.h
#define MODEL_INPUT_SIZE        784
#define MODEL_NUM_CLASSES       10
#define MODEL_INPUT_SCALE       0.00784314f
#define MODEL_INPUT_ZERO_POINT  -128
#define MODEL_OUTPUT_SCALE      0.00390625f
#define MODEL_OUTPUT_ZERO_POINT -128
```

---

## Step 3 — Build and Flash

### STM32N6570-DK

**Boot sequence:** ROM bootloader → FSBL (in XSPI @ `0x70000000`) → copies app to AXISRAM → runs classifier.

**Prerequisites:**

1. Generate C code from [ST Edge AI Developer Cloud](https://stedgeai-dc.st.com) (target: STM32N657) and copy the generated `Middlewares/ST/AI/` folder into `firmware/stm32n6/`.

2. Download the prebuilt FSBL from the [STM32N6-GettingStarted-ObjectDetection](https://github.com/STMicroelectronics/STM32N6-GettingStarted-ObjectDetection) repo and place it in `firmware/stm32n6/`:
   ```
   firmware/stm32n6/ai_fsbl_cut_2_0.stm32
   ```

**Build:**
```bash
cd firmware/stm32n6
cmake -B build -G Ninja
ninja -C build
```

**Flash** (signs app + flashes FSBL and classifier to XSPI NOR via STM32CubeProgrammer):
```bash
bash flash.sh build/classifier.elf
```

This flashes:
- FSBL → XSPI @ `0x70000000`
- Classifier (signed) → XSPI @ `0x70040000`

On reset the FSBL copies the classifier to AXISRAM at `0x34010000` and jumps to it. Results print via UART/RTT.

### ESP32-S3

**Prerequisites:** Clone the TFLite Micro ESP component once:

```bash
cd firmware/esp32
git clone https://github.com/espressif/esp-tflite-micro components/esp-tflite-micro
```

Then build and flash:

```bash
source /opt/esp-idf/export.sh
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### Arduino Nano 33 BLE Sense

```bash
arduino-cli compile \
    --fqbn arduino:mbed_nano:nano33ble \
    firmware/arduino/nano33_classifier

arduino-cli upload \
    --fqbn arduino:mbed_nano:nano33ble \
    -p /dev/ttyACM0 \
    firmware/arduino/nano33_classifier

arduino-cli monitor -p /dev/ttyACM0 --config baudrate=115200
```

---

## Collecting Results

Each board prints one CSV line to serial output:

```
platform,count,accuracy,avg_us,min_us,max_us
STM32N6,100,98.00,142,138,201
ESP32-S3,100,98.00,890,880,910
Arduino-Nano33,100,98.00,4200,4150,4300
```

Copy these lines into `results/benchmark_results.csv` and open `results/analysis.ipynb` to generate paper figures.

---

## Common Interface

All three platforms implement the same C API defined in `firmware/common/model_interface.h`:

```c
void     model_init(void);
void     model_run(const int8_t *input, int8_t *output);
uint32_t model_inference_time_us(void);
```

To port to a fourth platform: implement these three functions and provide a `model_config.h` — no other changes needed.

---

## Known Limitations

### STM32N6570-DK — Neural-ART NPU Not Used

The STM32N657 includes a Neural-ART NPU hardware accelerator. However, **DS-CNN-M is not compatible with the NPU** and runs on the Cortex-M55 CPU instead. The NPU rejected the model for the following reasons:

| Requirement | DS-CNN-M | Status |
|-------------|----------|--------|
| Standard Conv2D operators | Uses Depthwise Separable Conv | Not supported by NPU |
| Per-tensor int8 quantization | Uses per-channel quantization | NPU requires per-tensor |
| 2D spatial input (e.g. 224×224) | MFCC input is 49×10 (audio) | Suboptimal NPU mapping |
| Fused BN + activation layers | Separate layers in architecture | NPU requires fused ops |

The Neural-ART NPU is optimized for image classification CNNs (MobileNetV1/V2, ResNet variants) with standard spatial convolutions. Audio models with 1D-like MFCC inputs and depthwise separable convolutions do not map onto the NPU dataflow.

**Impact on benchmark:** STM32N6 results reflect Cortex-M55 CPU performance at 800 MHz, not NPU-accelerated inference. This is a valid and intentional comparison — it isolates the effect of CPU microarchitecture (M55 vs LX7 vs M4F) independent of dedicated hardware accelerators.

**Format note:** Both TFLite and ONNX formats were tested with ST Edge AI Developer Cloud. The NPU rejection is based on model architecture, not file format — the tool produces the same result for both.

**Future work:** Evaluating an NPU-compatible model (e.g. MobileNet-based KWS) on the Neural-ART accelerator would complement these results.

---

## Chip Reference

| Document | Title |
|----------|-------|
| RM0486 | STM32N657 Reference Manual |
| ESP32-S3 TRM | ESP32-S3 Technical Reference Manual |
| nRF52840 PS | nRF52840 Product Specification |
| ST Edge AI | [ST Edge AI Developer Cloud](https://stedgeai-dc.st.com) |
