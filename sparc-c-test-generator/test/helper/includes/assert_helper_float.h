#ifndef ASSERT_HELPER_FLOAT_H
#define ASSERT_HELPER_FLOAT_H

#include <math.h>

// ========== Float Type Equality Assertions ==========

void assert_float_equal(float actual, float expected);
void assert_float_equal_tolerance(float actual, float expected, float tolerance);
void assert_float_not_equal(float actual, float not_expected);

// ========== Float Range Assertions ==========

void assert_float_in_range(float actual, float min_val, float max_val);
void assert_float_not_in_range(float actual, float min_val, float max_val);

// ========== Float Comparison Assertions ==========

void assert_float_greater_than(float actual, float threshold);
void assert_float_less_than(float actual, float threshold);
void assert_float_greater_or_equal(float actual, float threshold);
void assert_float_less_or_equal(float actual, float threshold);

// ========== Special Float Assertions ==========

void assert_float_is_zero(float actual);
void assert_float_is_positive(float actual);
void assert_float_is_negative(float actual);
void assert_float_is_nan(float actual);
void assert_float_is_not_nan(float actual);
void assert_float_is_infinite(float actual);
void assert_float_is_not_infinite(float actual);
void assert_float_is_finite(float actual);

// ========== Float Array Assertions ==========

void assert_float_array_equal(float *actual, float *expected, int size);
void assert_float_array_equal_tolerance(float *actual, float *expected, int size, float tolerance);

#endif // ASSERT_HELPER_FLOAT_H
