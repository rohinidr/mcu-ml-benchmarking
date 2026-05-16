#pragma once

/* Fill in from: python model/convert.py --print-quant-params */
#define MODEL_INPUT_SIZE        784
#define MODEL_NUM_CLASSES       10

#define MODEL_INPUT_SCALE       0.0078125f
#define MODEL_INPUT_ZERO_POINT  -128

#define MODEL_OUTPUT_SCALE      0.00390625f
#define MODEL_OUTPUT_ZERO_POINT -128
