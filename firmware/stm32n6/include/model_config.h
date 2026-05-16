#pragma once

/*
 * Fill in these values from the output of:
 *   python model/convert.py --model <your_model> --print-quant-params
 */
#define MODEL_INPUT_SIZE        784     /* e.g. 28*28 for MNIST — update for your model */
#define MODEL_NUM_CLASSES       10      /* update for your dataset */

#define MODEL_INPUT_SCALE       0.0078125f
#define MODEL_INPUT_ZERO_POINT  -128

#define MODEL_OUTPUT_SCALE      0.00390625f
#define MODEL_OUTPUT_ZERO_POINT -128
