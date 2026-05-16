cmake_minimum_required(VERSION 3.16)

set(CMAKE_SYSTEM_NAME      Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER       arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER     arm-none-eabi-gcc)
set(CMAKE_OBJCOPY          arm-none-eabi-objcopy)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

project(classifier C ASM)

set(CPU_FLAGS "-mcpu=cortex-m55 -mfpu=none -mfloat-abi=soft -mthumb")
set(CMAKE_C_FLAGS   "${CPU_FLAGS} -Os -ffunction-sections -fdata-sections -Wall")
set(CMAKE_EXE_LINKER_FLAGS
    "${CPU_FLAGS} -T${CMAKE_SOURCE_DIR}/memory.x -Wl,--gc-sections -nostartfiles")

# ── Sources ────────────────────────────────────────────────────────────────
# After running ST Edge AI Developer Cloud, copy generated files here:
#   Middlewares/ST/AI/Src/network.c
#   Middlewares/ST/AI/Src/network_data.c
#   Middlewares/ST/AI/Lib/libNeuralART_CortexM55_GCC.a
file(GLOB AI_SRCS  Middlewares/ST/AI/Src/*.c)

add_executable(classifier
    src/main.c
    src/model_runner.c
    src/platform.c
    ${AI_SRCS}
)

# ── Include paths ──────────────────────────────────────────────────────────
target_include_directories(classifier PRIVATE
    include
    ../common
    Middlewares/ST/AI/Inc
)

# ── ST Neural-ART runtime (precompiled, from ST Edge AI download) ──────────
target_link_libraries(classifier PRIVATE
    ${CMAKE_SOURCE_DIR}/Middlewares/ST/AI/Lib/libNeuralART_CortexM55_GCC.a
)

# ── Post-build: flat binary for signing ───────────────────────────────────
add_custom_command(TARGET classifier POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary classifier.elf classifier.bin
    COMMENT "Generating classifier.bin"
)
