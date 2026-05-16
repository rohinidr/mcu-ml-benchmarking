#!/bin/bash
set -e

echo "==> System packages"
sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    gcc-arm-none-eabi gdb-multiarch \
    cmake ninja-build \
    libusb-1.0-0 libusb-1.0-0-dev \
    wget curl unzip git python3-pip \
    udev

echo "==> Python packages"
pip install --quiet \
    tensorflow \
    numpy pandas matplotlib scikit-learn \
    jupyterlab pillow tqdm \
    flatbuffers

echo "==> probe-rs (STM32N6 flash tool)"
cargo install probe-rs-tools --locked 2>/dev/null || echo "probe-rs already installed"

echo "==> Arduino CLI"
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh \
    | BINDIR=/usr/local/bin sh
arduino-cli core update-index
arduino-cli core install arduino:mbed_nano
arduino-cli lib install "Arduino_TensorFlowLite"

echo "==> ESP-IDF v5.3 (ESP32-S3)"
if [ ! -d /opt/esp-idf ]; then
    git clone --depth 1 -b v5.3 \
        https://github.com/espressif/esp-idf.git /opt/esp-idf
fi
/opt/esp-idf/install.sh esp32s3
echo 'source /opt/esp-idf/export.sh' >> ~/.bashrc

echo "==> Claude Code"
npm install -g @anthropic-ai/claude-code 2>/dev/null || true

echo "==> Done. Reopen terminal to activate ESP-IDF environment."
