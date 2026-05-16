#include <stdint.h>
#include <stdio.h>

/* SysTick at 1 MHz for microsecond timing.
 * Adjust SystemCoreClock to match your clock config. */
#define SYSTICK_RELOAD  (SystemCoreClock / 1000000U - 1U)

static volatile uint32_t tick_us;

void SysTick_Handler(void) { tick_us++; }

void platform_init(void)
{
    /* Enable SysTick at 1 us resolution */
    SysTick->LOAD  = SYSTICK_RELOAD;
    SysTick->VAL   = 0;
    SysTick->CTRL  = SysTick_CTRL_CLKSOURCE_Msk
                   | SysTick_CTRL_TICKINT_Msk
                   | SysTick_CTRL_ENABLE_Msk;

    /* UART init for printf — wire to probe-rs RTT or LPUART */
}

uint32_t platform_timer_us(void) { return tick_us; }

void benchmark_print_csv(const char *platform, const void *s_)
{
    /* Cast matches benchmark_stats_t in benchmark.h */
    const uint32_t *s = (const uint32_t *)s_;
    uint32_t count    = s[0];
    uint32_t correct  = s[1];
    uint64_t total    = *(uint64_t *)(s + 2);
    uint32_t min_us   = s[4];
    uint32_t max_us   = s[5];

    printf("%s,%lu,%.2f,%lu,%lu,%lu\n",
           platform, count,
           count ? 100.0f * correct / count : 0.0f,
           count ? (uint32_t)(total / count) : 0,
           min_us, max_us);
}
