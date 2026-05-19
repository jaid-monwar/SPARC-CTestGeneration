#ifndef ASSERT_HELPER_DOUBLE_H
#define ASSERT_HELPER_DOUBLE_H

#include <math.h>

// ========== Double Type Equality Assertions ==========

void assert_double_equal(double actual, double expected);
void assert_double_equal_tolerance(double actual, double expected, double tolerance);
void assert_double_not_equal(double actual, double not_expected);

// ========== Double Range Assertions ==========

void assert_double_in_range(double actual, double min_val, double max_val);
void assert_double_not_in_range(double actual, double min_val, double max_val);

// ========== Double Comparison Assertions ==========

void assert_double_greater_than(double actual, double threshold);
void assert_double_less_than(double actual, double threshold);
void assert_double_greater_or_equal(double actual, double threshold);
void assert_double_less_or_equal(double actual, double threshold);

// ========== Special Double Assertions ==========

void assert_double_is_zero(double actual);
void assert_double_is_positive(double actual);
void assert_double_is_negative(double actual);
void assert_double_is_nan(double actual);
void assert_double_is_not_nan(double actual);
void assert_double_is_infinite(double actual);
void assert_double_is_not_infinite(double actual);
void assert_double_is_finite(double actual);

// ========== Double Array Assertions ==========

void assert_double_array_equal(double *actual, double *expected, int size);
void assert_double_array_equal_tolerance(double *actual, double *expected, int size, double tolerance);

#endif // ASSERT_HELPER_DOUBLE_H
