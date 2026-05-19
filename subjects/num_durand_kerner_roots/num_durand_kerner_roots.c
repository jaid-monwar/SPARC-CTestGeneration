/**
 * @file
 * \brief Compute all possible approximate roots of any given polynomial using
 * [Durand Kerner
 * algorithm](https://en.wikipedia.org/wiki/Durand%E2%80%93Kerner_method)
 *
 * \author [Krishna Vedala](https://github.com/kvedala)
 * Modified for unit testing.
 */

#define _USE_MATH_DEFINES
#include <complex.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846264338327950288L
#endif

#define ACCURACY 1e-10 /**< maximum accuracy limit */

/**
 * Evaluate the value of a polynomial with given coefficients
 * \param[in] coeffs coefficients of the polynomial
 * \param[in] degree degree of polynomial
 * \param[in] x point at which to evaluate the polynomial
 * \returns \f$f(x)\f$
 */
long double complex poly_function(long double *coeffs, unsigned int degree,
                                  long double complex x)
{
    long double complex out = 0.;
    unsigned int n;

    if (coeffs == NULL || degree == 0) {
        return 0.;
    }

    for (n = 0; n < degree; n++) out += coeffs[n] * cpow(x, degree - n - 1);

    return out;
}

/**
 * Create a textual form of complex number
 * \param[in] x complex number to convert
 * \param[out] buffer output buffer (must be at least 50 chars)
 * \param[in] buffer_size size of the output buffer
 * \returns 0 on success, -1 on failure
 */
int complex_to_str(long double complex x, char *buffer, size_t buffer_size)
{
    if (buffer == NULL || buffer_size < 50) {
        return -1;
    }
    double r = creal(x);
    double c = cimag(x);
    snprintf(buffer, buffer_size, "% 7.04g%+7.04gj", r, c);
    return 0;
}

/**
 * Check for termination condition (stateless version for testing)
 * \param[in] delta current delta value
 * \param[in] past_delta previous delta value
 * \returns 0 if termination not reached
 * \returns 1 if termination reached
 */
int check_termination_stateless(long double delta, long double past_delta)
{
    if (fabsl(past_delta - delta) <= ACCURACY || delta < ACCURACY)
        return 1;
    return 0;
}

/**
 * Normalize polynomial coefficients by dividing by the leading coefficient
 * \param[in,out] coeffs coefficients array to normalize
 * \param[in] degree number of coefficients
 * \returns 0 on success, -1 on failure (null pointer or zero leading coeff)
 */
int normalize_coefficients(long double *coeffs, unsigned int degree)
{
    if (coeffs == NULL || degree == 0) {
        return -1;
    }
    if (coeffs[0] == 0.0L) {
        return -1;  // Cannot normalize with zero leading coefficient
    }

    long double leading = coeffs[0];
    for (unsigned int i = 0; i < degree; i++) {
        coeffs[i] /= leading;
    }
    return 0;
}

/**
 * Perform one iteration of the Durand-Kerner algorithm
 * \param[in] coeffs normalized polynomial coefficients
 * \param[in] degree polynomial degree (number of coefficients)
 * \param[in,out] roots array of root approximations (size: degree-1)
 * \param[out] max_delta maximum absolute change in any root
 * \returns 0 on success, -1 on failure, 1 on overflow/underflow
 */
int durand_kerner_iteration(long double *coeffs, unsigned int degree,
                            long double complex *roots, long double *max_delta)
{
    if (coeffs == NULL || roots == NULL || max_delta == NULL) {
        return -1;
    }
    if (degree < 2) {
        return -1;  // Need at least degree 2 for roots
    }

    unsigned int num_roots = degree - 1;
    *max_delta = 0;

    for (unsigned int n = 0; n < num_roots; n++) {
        long double complex numerator = poly_function(coeffs, degree, roots[n]);
        long double complex denominator = 1.0;

        for (unsigned int i = 0; i < num_roots; i++) {
            if (i != n) {
                denominator *= roots[n] - roots[i];
            }
        }

        long double complex delta = numerator / denominator;
        long double abs_delta = cabsl(delta);

        if (isnan(abs_delta) || isinf(abs_delta)) {
            return 1;  // Overflow/underflow
        }

        roots[n] -= delta;

        if (fabsl(abs_delta) > *max_delta) {
            *max_delta = fabsl(abs_delta);
        }
    }

    return 0;
}

/**
 * Initialize root approximations with distinct values on the unit circle
 * \param[out] roots array to store initial root approximations
 * \param[in] num_roots number of roots (degree - 1)
 * \param[in] seed random seed (0 for deterministic initialization)
 * \returns 0 on success, -1 on failure
 */
int initialize_roots(long double complex *roots, unsigned int num_roots, unsigned int seed)
{
    if (roots == NULL || num_roots == 0) {
        return -1;
    }

    if (seed == 0) {
        // Deterministic initialization: evenly spaced on unit circle
        for (unsigned int i = 0; i < num_roots; i++) {
            long double angle = 2.0L * M_PI * i / num_roots;
            roots[i] = cosl(angle) + sinl(angle) * I;
        }
    } else {
        // Random initialization
        srand(seed);
        for (unsigned int i = 0; i < num_roots; i++) {
            roots[i] = (long double)rand() / RAND_MAX +
                       ((long double)rand() / RAND_MAX) * I;
        }
    }

    return 0;
}

/**
 * Find all roots of a polynomial using the Durand-Kerner method
 * \param[in] coeffs polynomial coefficients (will be normalized internally)
 * \param[in] degree number of coefficients
 * \param[out] roots output array for roots (must have size degree-1)
 * \param[in] max_iterations maximum number of iterations
 * \param[out] iterations_used actual number of iterations performed (can be NULL)
 * \returns 0 on success, -1 on failure, 1 on overflow/underflow, 2 on max iterations
 */
int find_polynomial_roots(long double *coeffs, unsigned int degree,
                          long double complex *roots, unsigned int max_iterations,
                          unsigned int *iterations_used)
{
    if (coeffs == NULL || roots == NULL || degree < 2) {
        return -1;
    }

    // Create a copy of coefficients to normalize
    long double *norm_coeffs = (long double *)malloc(degree * sizeof(long double));
    if (norm_coeffs == NULL) {
        return -1;
    }
    memcpy(norm_coeffs, coeffs, degree * sizeof(long double));

    if (normalize_coefficients(norm_coeffs, degree) != 0) {
        free(norm_coeffs);
        return -1;
    }

    // Initialize roots
    if (initialize_roots(roots, degree - 1, 0) != 0) {
        free(norm_coeffs);
        return -1;
    }

    long double past_delta = INFINITY;
    unsigned int iter = 0;
    int result = 0;

    while (iter < max_iterations) {
        long double max_delta;
        int iter_result = durand_kerner_iteration(norm_coeffs, degree, roots, &max_delta);

        if (iter_result == 1) {
            result = 1;  // Overflow/underflow
            break;
        } else if (iter_result != 0) {
            result = -1;
            break;
        }

        iter++;

        if (check_termination_stateless(max_delta, past_delta)) {
            break;
        }
        past_delta = max_delta;
    }

    if (iterations_used != NULL) {
        *iterations_used = iter;
    }

    if (result == 0 && iter >= max_iterations) {
        result = 2;  // Max iterations reached
    }

    free(norm_coeffs);
    return result;
}

/**
 * Verify if a value is approximately a root of the polynomial
 * \param[in] coeffs polynomial coefficients
 * \param[in] degree number of coefficients
 * \param[in] root the value to check
 * \param[in] tolerance acceptable tolerance for |f(root)|
 * \returns 1 if root is valid within tolerance, 0 otherwise
 */
int verify_root(long double *coeffs, unsigned int degree,
                long double complex root, long double tolerance)
{
    if (coeffs == NULL || degree == 0) {
        return 0;
    }

    long double complex value = poly_function(coeffs, degree, root);
    long double abs_value = cabsl(value);

    return (abs_value <= tolerance) ? 1 : 0;
}

/**
 * Count valid roots within tolerance
 * \param[in] coeffs polynomial coefficients
 * \param[in] degree number of coefficients
 * \param[in] roots array of root candidates
 * \param[in] num_roots number of roots to check
 * \param[in] tolerance acceptable tolerance
 * \returns number of valid roots
 */
unsigned int count_valid_roots(long double *coeffs, unsigned int degree,
                               long double complex *roots, unsigned int num_roots,
                               long double tolerance)
{
    if (coeffs == NULL || roots == NULL) {
        return 0;
    }

    unsigned int count = 0;
    for (unsigned int i = 0; i < num_roots; i++) {
        if (verify_root(coeffs, degree, roots[i], tolerance)) {
            count++;
        }
    }
    return count;
}

/**
 * Get the real part of a complex root
 * \param[in] root the complex root
 * \returns real part
 */
long double get_root_real(long double complex root)
{
    return creall(root);
}

/**
 * Get the imaginary part of a complex root
 * \param[in] root the complex root
 * \returns imaginary part
 */
long double get_root_imag(long double complex root)
{
    return cimagl(root);
}

/**
 * Check if a root is approximately real (imaginary part near zero)
 * \param[in] root the complex root
 * \param[in] tolerance tolerance for considering imaginary part as zero
 * \returns 1 if root is approximately real, 0 otherwise
 */
int is_root_real(long double complex root, long double tolerance)
{
    return (fabsl(cimagl(root)) <= tolerance) ? 1 : 0;
}

/**
 * Count how many roots are approximately real
 * \param[in] roots array of roots
 * \param[in] num_roots number of roots
 * \param[in] tolerance tolerance for imaginary part
 * \returns number of approximately real roots
 */
unsigned int count_real_roots(long double complex *roots, unsigned int num_roots,
                              long double tolerance)
{
    if (roots == NULL) {
        return 0;
    }

    unsigned int count = 0;
    for (unsigned int i = 0; i < num_roots; i++) {
        if (is_root_real(roots[i], tolerance)) {
            count++;
        }
    }
    return count;
}
