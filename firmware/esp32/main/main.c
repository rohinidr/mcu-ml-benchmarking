#include <stdio.h>
#include "model_interface.h"
#include "benchmark.h"

extern const int8_t  test_inputs[][MODEL_INPUT_SIZE];
extern const int     test_labels[];
extern const int     TEST_COUNT;

void app_main(void)
{
    model_init();

    benchmark_stats_t stats;
    benchmark_stats_init(&stats);

    for (int i = 0; i < TEST_COUNT; i++) {
        int8_t output[MODEL_NUM_CLASSES];
        model_run(test_inputs[i], output);

        benchmark_result_t r = {
            .inference_time_us = model_inference_time_us(),
            .predicted_class   = model_argmax(output),
            .true_label        = test_labels[i],
            .confidence        = model_dequantize(output[model_argmax(output)]),
        };
        benchmark_stats_update(&stats, &r);
    }

    benchmark_print_csv("ESP32-S3", &stats);
}
