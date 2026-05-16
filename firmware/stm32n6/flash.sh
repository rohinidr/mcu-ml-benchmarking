#!/bin/bash
# Flash FSBL + classifier to STM32N6570-DK via STM32CubeProgrammer.
#
# Prerequisites:
#   1. Build the ELF:  cmake -B build -G Ninja && ninja -C build
#   2. Download the ST prebuilt FSBL from the STM32N6 getting-started repo:
#        https://github.com/STMicroelectronics/STM32N6-GettingStarted-ObjectDetection
#      Copy ai_fsbl_cut_2_0.stm32 into this directory (firmware/stm32n6/).
#
# Usage:
#   bash flash.sh build/classifier.elf
set -e

ELF="${1:-build/classifier.elf}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

BASE=/home/vscode/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin
CLI="${STM32_PROGRAMMER_CLI:-$BASE/STM32_Programmer_CLI}"
SIGN="${STM32_SIGNING_CLI:-/home/vscode/stm32-signing/bin/STM32_SigningTool_CLI}"
LOADER="$BASE/ExternalLoader/MX66UW1G45G_STM32N6570-DK.stldr"
FSBL="$SCRIPT_DIR/ai_fsbl_cut_2_0.stm32"

for tool in "$CLI" "$SIGN"; do
    [ -x "$tool" ] || { echo "Error: $tool not found."; exit 1; }
done
[ -f "$FSBL" ] || {
    echo "Error: FSBL not found at $FSBL"
    echo "Download ai_fsbl_cut_2_0.stm32 from:"
    echo "  https://github.com/STMicroelectronics/STM32N6-GettingStarted-ObjectDetection"
    echo "and place it in firmware/stm32n6/"
    exit 1
}

# Get entry point from ELF header
EP=$(python3 -c "
import struct
data = open('$ELF','rb').read()
ep = struct.unpack_from('<I', data, 0x18)[0]
print(f'0x{ep:08x}')
")

BIN=$(mktemp /tmp/classifier_XXXXXX.bin)
SIGNED=$(mktemp /tmp/classifier_signed_XXXXXX.stm32)
trap 'rm -f "$BIN" "$SIGNED"' EXIT

arm-none-eabi-objcopy -O binary "$ELF" "$BIN"

echo "Signing classifier (load=0x34010000, entry=$EP)..."
"$SIGN" -bin "$BIN" -nk -t fsbl \
        -hv 2.3 -iv 1 \
        -la 0x34010000 -ep "$EP" \
        -of 0x80000000 \
        -align \
        -o "$SIGNED" -s

echo "Flashing FSBL @ 0x70000000 ..."
"$CLI" -c port=SWD mode=UR -el "$LOADER" \
    -d "$FSBL"   0x70000000 -v

echo "Flashing classifier @ 0x70040000 ..."
"$CLI" -c port=SWD mode=UR -el "$LOADER" \
    -d "$SIGNED" 0x70040000 -v -rst

echo "Done."
