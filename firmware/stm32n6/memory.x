/* STM32N657 — app stored in XSPI NOR, copied to NS AXISRAM by FSBL
 *
 * NS AXISRAM total: 0x34000000–0x343BFFFF (3.8 MiB)
 *
 * FSBL load address : 0x34010000
 * FLASH (code + model weights) : 1.5 MiB → ends at 0x34190000
 * RAM   (data + activations + stack) : 1.5 MiB → ends at 0x34310000
 *
 * Regions must not overlap. Total used: 3 MiB < 3.8 MiB available.
 */
MEMORY
{
    FLASH : ORIGIN = 0x34010000, LENGTH = 1536K
    RAM   : ORIGIN = 0x34190000, LENGTH = 1536K
}
