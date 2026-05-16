#pragma once
#include <stdint.h>

/*
 * Common inference API — implemented identically on all three targets.
 * Each platform provides model_config.h defining the constants below.
 *
 * Workflow:
 *   1. model/convert.py prints MODEL_INPUT_SIZE, scale, zero_point values.
 *   2. Copy them into firmware/<target>/include/model_config.h.
 *   3. Compile — no other changes needed.
 */

#include "model_config.h"   /* platform-specific: defines constants below */

/*
 * Required in model_config.h:
 *
 *   #define MODEL_INPUT_SIZE       <int>    // total input elements (e.g. 28*28 = 784)
 *   #define MODEL_NUM_CLASSES      <int>    // number of output classes
 *   #define MODEL_INPUT_SCALE      <float>  // from TFLite converter
 *   #define MODEL_INPUT_ZERO_POINT <int>    // from TFLite converter
 *   #define MODEL_OUTPUT_SCALE     <float>  // from TFLite converter
 *   #define MODEL_OUTPUT_ZERO_POINT <int>   // from TFLite converter
 */

/* Initialize model runtime — call once in main(). */
void model_init(void);

/* Run one inference.
 *   input  : int8_t[MODEL_INPUT_SIZE]  — quantized input
 *   output : int8_t[MODEL_NUM_CLASSES] — raw quantized logits
 */
void model_run(const int8_t *input, int8_t *output);

/* Microseconds spent in the last model_run() call. */
uint32_t model_inference_time_us(void);

/* Helper: dequantize a single int8 output value to float probability. */
static inline float model_dequantize(int8_t val)
{
    return MODEL_OUTPUT_SCALE * (val - MODEL_OUTPUT_ZERO_POINT);
}

/* Helper: return index of highest logit (argmax). */
static inline int model_argmax(const int8_t *output)
{
    int best = 0;
    for (int i = 1; i < MODEL_NUM_CLASSES; i++) {
        if (output[i] > output[best]) best = i;
    }
    return best;
}
