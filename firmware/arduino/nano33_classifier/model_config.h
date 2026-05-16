#pragma once

/* DS-CNN-M — Google Speech Commands v2 (35 keywords)
 * Input: 49 MFCC frames × 10 coefficients = 490 int8 values
 * Source: model/dscnn_int8.tflite
 */
#define MODEL_INPUT_SIZE        490
#define MODEL_NUM_CLASSES       35

/* Update from: python model/convert.py --model model/dscnn_int8.tflite --print-quant-params */
#define MODEL_INPUT_SCALE       0.0078125f
#define MODEL_INPUT_ZERO_POINT  -128

#define MODEL_OUTPUT_SCALE      0.00390625f
#define MODEL_OUTPUT_ZERO_POINT -128
