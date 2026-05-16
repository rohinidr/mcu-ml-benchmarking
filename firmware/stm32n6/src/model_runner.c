#include "model_interface.h"
#include "network.h"          /* ST Edge AI generated */
#include "network_data.h"     /* ST Edge AI generated weights */
#include <cortex_m_systick.h> /* or platform timer — see platform.h */

static ai_handle    network;
static ai_u8        activations[AI_NETWORK_DATA_ACTIVATIONS_SIZE];
static uint32_t     last_inference_us;

void model_init(void)
{
    ai_network_create_and_init(&network, activations, NULL);
}

void model_run(const int8_t *input, int8_t *output)
{
    ai_buffer ai_input[AI_NETWORK_IN_NUM]   = AI_NETWORK_IN_1_ARGS(input);
    ai_buffer ai_output[AI_NETWORK_OUT_NUM] = AI_NETWORK_OUT_1_ARGS(output);

    uint32_t t0 = platform_timer_us();
    ai_network_run(network, ai_input, ai_output);
    last_inference_us = platform_timer_us() - t0;
}

uint32_t model_inference_time_us(void)
{
    return last_inference_us;
}
