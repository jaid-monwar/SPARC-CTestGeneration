/**
 * @file header.h
 * @brief Header file for Durand-Kerner polynomial root finding algorithm
 */

#ifndef NUM_DURAND_KERNER_ROOTS_H
#define NUM_DURAND_KERNER_ROOTS_H

#include <complex.h>
#include <stddef.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846264338327950288L
#endif

#define ACCURACY 1e-10 /**< maximum accuracy limit */

/**
 * Evaluate the value of a polynomial with given coefficients
 * @param coeffs coefficients of the polynomial
 * @param degree degree of polynomial
 * @param x point at which to evaluate the polynomial
 * @returns f(x)
 */
long double complex poly_function(long double *coeffs, unsigned int degree,
                                  long double complex x);

/**
 * Create a textual form of complex number
 * @param x complex number to convert
 * @param buffer output buffer (must be at least 50 chars)
 * @param buffer_size size of the output buffer
 * @returns 0 on success, -1 on failure
 */
int complex_to_str(long double complex x, char *buffer, size_t buffer_size);

/**
 * Check for termination condition (stateless version for testing)
 * @param delta current delta value
 * @param past_delta previous delta value
 * @returns 0 if termination not reached, 1 if termination reached
 */
int check_termination_stateless(long double delta, long double past_delta);

/**
 * Normalize polynomial coefficients by dividing by the leading coefficient
 * @param coeffs coefficients array to normalize
 * @param degree number of coefficients
 * @returns 0 on success, -1 on failure (null pointer or zero leading coeff)
 */
int normalize_coefficients(long double *coeffs, unsigned int degree);

/**
 * Perform one iteration of the Durand-Kerner algorithm
 * @param coeffs normalized polynomial coefficients
 * @param degree polynomial degree (number of coefficients)
 * @param roots array of root approximations (size: degree-1)
 * @param max_delta output: maximum absolute change in any root
 * @returns 0 on success, -1 on failure, 1 on overflow/underflow
 */
int durand_kerner_iteration(long double *coeffs, unsigned int degree,
                            long double complex *roots, long double *max_delta);

/**
 * Initialize root approximations with distinct values on the unit circle
 * @param roots array to store initial root approximations
 * @param num_roots number of roots (degree - 1)
 * @param seed random seed (0 for deterministic initialization)
 * @returns 0 on success, -1 on failure
 */
int initialize_roots(long double complex *roots, unsigned int num_roots, unsigned int seed);

/**
 * Find all roots of a polynomial using the Durand-Kerner method
 * @param coeffs polynomial coefficients (will be normalized internally)
 * @param degree number of coefficients
 * @param roots output array for roots (must have size degree-1)
 * @param max_iterations maximum number of iterations
 * @param iterations_used output: actual number of iterations performed (can be NULL)
 * @returns 0 on success, -1 on failure, 1 on overflow/underflow, 2 on max iterations
 */
int find_polynomial_roots(long double *coeffs, unsigned int degree,
                          long double complex *roots, unsigned int max_iterations,
                          unsigned int *iterations_used);

/**
 * Verify if a value is approximately a root of the polynomial
 * @param coeffs polynomial coefficients
 * @param degree number of coefficients
 * @param root the value to check
 * @param tolerance acceptable tolerance for |f(root)|
 * @returns 1 if root is valid within tolerance, 0 otherwise
 */
int verify_root(long double *coeffs, unsigned int degree,
                long double complex root, long double tolerance);

/**
 * Count valid roots within tolerance
 * @param coeffs polynomial coefficients
 * @param degree number of coefficients
 * @param roots array of root candidates
 * @param num_roots number of roots to check
 * @param tolerance acceptable tolerance
 * @returns number of valid roots
 */
unsigned int count_valid_roots(long double *coeffs, unsigned int degree,
                               long double complex *roots, unsigned int num_roots,
                               long double tolerance);

/**
 * Get the real part of a complex root
 * @param root the complex root
 * @returns real part
 */
long double get_root_real(long double complex root);

/**
 * Get the imaginary part of a complex root
 * @param root the complex root
 * @returns imaginary part
 */
long double get_root_imag(long double complex root);

/**
 * Check if a root is approximately real (imaginary part near zero)
 * @param root the complex root
 * @param tolerance tolerance for considering imaginary part as zero
 * @returns 1 if root is approximately real, 0 otherwise
 */
int is_root_real(long double complex root, long double tolerance);

/**
 * Count how many roots are approximately real
 * @param roots array of roots
 * @param num_roots number of roots
 * @param tolerance tolerance for imaginary part
 * @returns number of approximately real roots
 */
unsigned int count_real_roots(long double complex *roots, unsigned int num_roots,
                              long double tolerance);

#endif /* NUM_DURAND_KERNER_ROOTS_H */
