/**
 * @file header.h
 * @brief Header file for Forward Euler ODE solver
 *
 * Solves a multivariable first order ordinary differential equation (ODE)
 * using the forward Euler method.
 */

#ifndef NUM_ODE_FORWARD_EULER_H
#define NUM_ODE_FORWARD_EULER_H

#include <math.h>
#include <stdlib.h>

/** Number of dependent variables in the ODE system */
#define order 2

/* ============= Core ODE Functions ============= */

/**
 * @brief Problem statement for a system with first-order differential equations.
 * Updates the system differential variables.
 *
 * @param[in]      x   independent variable(s)
 * @param[in,out]  y   dependent variable(s)
 * @param[in,out]  dy  first-derivative of dependent variable(s)
 */
void problem(const double *x, double *y, double *dy);

/**
 * @brief Exact solution of the problem. Used for solution comparison.
 *
 * @param[in]      x   independent variable
 * @param[in,out]  y   dependent variable
 */
void exact_solution(const double *x, double *y);

/**
 * @brief Compute next step approximation using the forward-Euler method.
 * y_{n+1} = y_n + dx * f(x_n, y_n)
 *
 * @param[in]      dx  step size
 * @param[in,out]  x   take x_n and compute x_{n+1}
 * @param[in,out]  y   take y_n and compute y_{n+1}
 * @param[in,out]  dy  compute f(x_n, y_n)
 */
void forward_euler_step(const double dx, const double *x, double *y, double *dy);

/**
 * @brief Compute approximation using the forward-Euler method in the given limits.
 *
 * @param[in]      dx     step size
 * @param[in]      x0     initial value of independent variable
 * @param[in]      x_max  final value of independent variable
 * @param[in,out]  y      take y_n and compute y_{n+1}
 * @returns number of iterations performed, or -1 on error
 */
int forward_euler(double dx, double x0, double x_max, double *y);

/**
 * @brief Compute approximation and store results in provided arrays.
 *
 * @param[in]      dx          step size
 * @param[in]      x0          initial value of independent variable
 * @param[in]      x_max       final value of independent variable
 * @param[in,out]  y           take y_n and compute y_{n+1}
 * @param[out]     x_results   array to store x values (must be pre-allocated)
 * @param[out]     y0_results  array to store y[0] values (must be pre-allocated)
 * @param[out]     y1_results  array to store y[1] values (must be pre-allocated)
 * @param[in]      max_results maximum number of results to store
 * @returns number of iterations performed, or -1 on error
 */
int forward_euler_with_results(double dx, double x0, double x_max, double *y,
                               double *x_results, double *y0_results,
                               double *y1_results, int max_results);

/* ============= Utility Functions for Testing ============= */

/**
 * @brief Check if two double values are approximately equal within a tolerance.
 *
 * @param[in] a         first value
 * @param[in] b         second value
 * @param[in] tolerance maximum allowed difference
 * @returns 1 if approximately equal, 0 otherwise
 */
int doubles_are_close(double a, double b, double tolerance);

/**
 * @brief Compute the absolute error between numerical and exact solution.
 *
 * @param[in] numerical computed value
 * @param[in] exact     exact value
 * @returns absolute error
 */
double compute_absolute_error(double numerical, double exact);

/**
 * @brief Compute the relative error between numerical and exact solution.
 *
 * @param[in] numerical computed value
 * @param[in] exact     exact value
 * @returns relative error, or -1 if exact is zero
 */
double compute_relative_error(double numerical, double exact);

/**
 * @brief Validate that the numerical solution stays bounded.
 *
 * @param[in] y     solution array
 * @param[in] bound maximum allowed magnitude
 * @returns 1 if bounded, 0 if unbounded
 */
int solution_is_bounded(const double *y, double bound);

/**
 * @brief Compute the expected number of iterations for given parameters.
 *
 * @param[in] dx    step size
 * @param[in] x0    initial x value
 * @param[in] x_max final x value
 * @returns expected number of iterations
 */
int compute_expected_iterations(double dx, double x0, double x_max);

/**
 * @brief Initialize the default initial conditions for the ODE.
 *
 * @param[out] y array to store initial conditions (must have at least 2 elements)
 */
void init_default_conditions(double *y);

/**
 * @brief Copy solution array.
 *
 * @param[in]  src  source array
 * @param[out] dest destination array
 */
void copy_solution(const double *src, double *dest);

/**
 * @brief Check if solution satisfies energy conservation (for harmonic oscillator).
 * For the harmonic oscillator with omega=1, the energy E = u^2 + v^2 should be constant.
 *
 * @param[in] y              solution array
 * @param[in] initial_energy expected energy (should be 1.0 for default initial conditions)
 * @param[in] tolerance      maximum allowed deviation
 * @returns 1 if energy is conserved, 0 otherwise
 */
int check_energy_conservation(const double *y, double initial_energy, double tolerance);

#endif /* NUM_ODE_FORWARD_EULER_H */
