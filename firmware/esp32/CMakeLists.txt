cmake_minimum_required(VERSION 3.16)

# Clone TFLite Micro ESP component if not present:
#   git clone https://github.com/espressif/esp-tflite-micro components/esp-tflite-micro

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(classifier)
