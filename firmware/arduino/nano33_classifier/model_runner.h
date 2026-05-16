#pragma once
#include <stdint.h>

void     model_init(void);
void     model_run(const int8_t *input, int8_t *output);
uint32_t model_inference_time_us(void);
