#ifndef ASSERT_HELPER_INTEGER_H
#define ASSERT_HELPER_INTEGER_H

#include <stdint.h>

// ========== Integer Type Equality Assertions ==========

void assert_int_equal(int actual, int expected);
void assert_uint8_equal(uint8_t actual, uint8_t expected);
void assert_uint16_equal(uint16_t actual, uint16_t expected);
void assert_uint32_equal(uint32_t actual, uint32_t expected);
void assert_uint64_equal(uint64_t actual, uint64_t expected);
void assert_int8_equal(int8_t actual, int8_t expected);
void assert_int16_equal(int16_t actual, int16_t expected);
void assert_int32_equal(int32_t actual, int32_t expected);
void assert_int64_equal(int64_t actual, int64_t expected);

// ========== Integer Range Assertions ==========

void assert_int_in_range(int actual, int min_val, int max_val);
void assert_uint8_in_range(uint8_t actual, uint8_t min_val, uint8_t max_val);
void assert_uint32_in_range(uint32_t actual, uint32_t min_val, uint32_t max_val);

// ========== Integer Comparison Assertions ==========

void assert_int_greater_than(int actual, int threshold);
void assert_int_less_than(int actual, int threshold);
void assert_uint32_greater_than(uint32_t actual, uint32_t threshold);
void assert_uint8_greater_than(uint8_t actual, uint8_t threshold);

// ========== Special Integer Assertions ==========

void assert_int_non_zero(int actual);
void assert_int_positive(int actual);
void assert_int_negative(int actual);
void assert_uint_is_zero(uint32_t actual);

#endif // ASSERT_HELPER_INTEGER_H
