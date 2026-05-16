#pragma once
#include <stdint.h>
#include "model_interface.h"

/* Single inference result — same struct logged on all platforms. */
typedef struct {
    uint32_t inference_time_us;
    int      predicted_class;
    int      true_label;        /* -1 if unknown */
    float    confidence;        /* dequantized score of predicted class */
} benchmark_result_t;

/* Running statistics accumulated across N inferences. */
typedef struct {
    uint32_t count;
    uint32_t correct;
    uint64_t total_time_us;
    uint32_t min_time_us;
    uint32_t max_time_us;
} benchmark_stats_t;

static inline void benchmark_stats_init(benchmark_stats_t *s)
{
    s->count        = 0;
    s->correct      = 0;
    s->total_time_us = 0;
    s->min_time_us  = UINT32_MAX;
    s->max_time_us  = 0;
}

static inline void benchmark_stats_update(benchmark_stats_t *s,
                                           const benchmark_result_t *r)
{
    s->count++;
    if (r->true_label >= 0 && r->predicted_class == r->true_label)
        s->correct++;
    s->total_time_us += r->inference_time_us;
    if (r->inference_time_us < s->min_time_us) s->min_time_us = r->inference_time_us;
    if (r->inference_time_us > s->max_time_us) s->max_time_us = r->inference_time_us;
}

/* Print CSV row: platform,count,accuracy,avg_us,min_us,max_us
 * Implemented per platform (UART printf or USB serial). */
void benchmark_print_csv(const char *platform, const benchmark_stats_t *s);
