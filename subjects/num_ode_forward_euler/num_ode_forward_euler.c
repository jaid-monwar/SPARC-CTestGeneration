/**
 * \file
 * \authors [Krishna Vedala](https://github.com/kvedala)
 * \brief Solve a multivariable first order [ordinary differential equation
 * (ODEs)](https://en.wikipedia.org/wiki/Ordinary_differential_equation) using
 * [forward Euler
 * method](https://en.wikipedia.org/wiki/Numerical_methods_for_ordinary_differential_equations#Euler_method)
 *
 * \details
 * The ODE being solved is:
 * \f{eqnarray*}{
 * \dot{u} &=& v\\
 * \dot{v} &=& -\omega^2 u\\
 * \omega &=& 1\\
 * [x_0, u_0, v_0] &=& [0,1,0]\qquad\ldots\text{(initial values)}
 * \f}
 * The exact solution for the above problem is:
 * \f{eqnarray*}{
 * u(x) &=& \cos(x)\\
 * v(x) &=& -\sin(x)\\
 * \f}
 * The computation results are stored to a text file `forward_euler.csv` and the
 * exact soltuion results in `exact.csv` for comparison.
 * <img
 * src="https://raw.githubusercontent.com/TheAlgorithms/C/docs/images/numerical_methods/ode_forward_euler.svg"
 * alt="Implementation solution"/>
 *
 * To implement [Van der Pol
 * oscillator](https://en.wikipedia.org/wiki/Van_der_Pol_oscillator), change the
 * ::problem function to:
 * ```cpp
 * const double mu = 2.0;
 * dy[0] = y[1];
 * dy[1] = mu * (1.f - y[0] * y[0]) * y[1] - y[0];
 * ```
 * \see ode_midpoint_euler.c, ode_semi_implicit_euler.c
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define order 2 /**< number of dependent variables in ::problem */

/**
 * @brief Problem statement for a system with first-order differential
 * equations. Updates the system differential variables.
 * \note This function can be updated to and ode of any order.
 *
 * @param[in] 		x 		independent variable(s)
 * @param[in,out]	y		dependent variable(s)
 * @param[in,out]	dy	    first-derivative of dependent variable(s)
 */
void problem(const double *x, double *y, double *dy)
{
    const double omega = 1.F;       // some const for the problem
    dy[0] = y[1];                   // x dot
    dy[1] = -omega * omega * y[0];  // y dot
}

/**
 * @brief Exact solution of the problem. Used for solution comparison.
 *
 * @param[in] 		x 		independent variable
 * @param[in,out]	y		dependent variable
 */
void exact_solution(const double *x, double *y)
{
    y[0] = cos(x[0]);
    y[1] = -sin(x[0]);
}

/**
 * @brief Compute next step approximation using the forward-Euler
 * method. @f[y_{n+1}=y_n + dx\cdot f\left(x_n,y_n\right)@f]
 * @param[in] 		dx	step size
 * @param[in,out] 	x	take \f$x_n\f$ and compute \f$x_{n+1}\f$
 * @param[in,out] 	y	take \f$y_n\f$ and compute \f$y_{n+1}\f$
 * @param[in,out]	dy	compute \f$f\left(x_n,y_n\right)\f$
 */
void forward_euler_step(const double dx, const double *x, double *y, double *dy)
{
    int o;
    problem(x, y, dy);
    for (o = 0; o < order; o++) y[o] += dx * dy[o];
}

/**
 * @brief Compute approximation using the forward-Euler
 * method in the given limits.
 * @param[in] 		dx  	step size
 * @param[in]   	x0  	initial value of independent variable
 * @param[in] 	    x_max	final value of independent variable
 * @param[in,out] 	y	    take \f$y_n\f$ and compute \f$y_{n+1}\f$
 * @returns number of iterations performed
 */
int forward_euler(double dx, double x0, double x_max, double *y)
{
    double dy[order];
    int iterations = 0;

    if (dx <= 0) {
        return -1;  // Invalid step size
    }

    /* start integration */
    double x = x0;
    do  // iterate for each step of independent variable
    {
        forward_euler_step(dx, &x, y, dy);  // perform integration
        x += dx;                            // update step
        iterations++;
    } while (x <= x_max);  // till upper limit of independent variable
    /* end of integration */

    return iterations;
}

/**
 * @brief Compute approximation and store results in provided arrays.
 * @param[in] 		dx  	step size
 * @param[in]   	x0  	initial value of independent variable
 * @param[in] 	    x_max	final value of independent variable
 * @param[in,out] 	y	    take \f$y_n\f$ and compute \f$y_{n+1}\f$
 * @param[out]      x_results   array to store x values (must be pre-allocated)
 * @param[out]      y0_results  array to store y[0] values (must be pre-allocated)
 * @param[out]      y1_results  array to store y[1] values (must be pre-allocated)
 * @param[in]       max_results maximum number of results to store
 * @returns number of iterations performed, or -1 on error
 */
int forward_euler_with_results(double dx, double x0, double x_max, double *y,
                               double *x_results, double *y0_results,
                               double *y1_results, int max_results)
{
    double dy[order];
    int iterations = 0;

    if (dx <= 0 || y == NULL) {
        return -1;  // Invalid parameters
    }

    /* start integration */
    double x = x0;
    do  // iterate for each step of independent variable
    {
        // Store results if arrays provided and space available
        if (x_results && y0_results && y1_results && iterations < max_results) {
            x_results[iterations] = x;
            y0_results[iterations] = y[0];
            y1_results[iterations] = y[1];
        }
        forward_euler_step(dx, &x, y, dy);  // perform integration
        x += dx;                            // update step
        iterations++;
    } while (x <= x_max);  // till upper limit of independent variable
    /* end of integration */

    return iterations;
}

/* ============= Utility functions for test assertions ============= */

/**
 * @brief Check if two double values are approximately equal within a tolerance.
 * @param[in] a         first value
 * @param[in] b         second value
 * @param[in] tolerance maximum allowed difference
 * @returns 1 if approximately equal, 0 otherwise
 */
int doubles_are_close(double a, double b, double tolerance)
{
    double diff = a - b;
    if (diff < 0) diff = -diff;
    return diff <= tolerance;
}

/**
 * @brief Compute the absolute error between numerical and exact solution.
 * @param[in] numerical computed value
 * @param[in] exact     exact value
 * @returns absolute error
 */
double compute_absolute_error(double numerical, double exact)
{
    double diff = numerical - exact;
    return diff < 0 ? -diff : diff;
}

/**
 * @brief Compute the relative error between numerical and exact solution.
 * @param[in] numerical computed value
 * @param[in] exact     exact value
 * @returns relative error, or -1 if exact is zero
 */
double compute_relative_error(double numerical, double exact)
{
    if (exact == 0.0) {
        return numerical == 0.0 ? 0.0 : -1.0;  // Handle division by zero
    }
    double diff = numerical - exact;
    if (diff < 0) diff = -diff;
    double abs_exact = exact < 0 ? -exact : exact;
    return diff / abs_exact;
}

/**
 * @brief Validate that the numerical solution stays bounded.
 * @param[in] y     solution array
 * @param[in] bound maximum allowed magnitude
 * @returns 1 if bounded, 0 if unbounded
 */
int solution_is_bounded(const double *y, double bound)
{
    if (y == NULL) return 0;
    double y0_abs = y[0] < 0 ? -y[0] : y[0];
    double y1_abs = y[1] < 0 ? -y[1] : y[1];
    return (y0_abs <= bound) && (y1_abs <= bound);
}

/**
 * @brief Compute the expected number of iterations for given parameters.
 * @param[in] dx    step size
 * @param[in] x0    initial x value
 * @param[in] x_max final x value
 * @returns expected number of iterations
 */
int compute_expected_iterations(double dx, double x0, double x_max)
{
    if (dx <= 0) return -1;
    int count = 0;
    double x = x0;
    do {
        x += dx;
        count++;
    } while (x <= x_max);
    return count;
}

/**
 * @brief Initialize the default initial conditions for the ODE.
 * @param[out] y array to store initial conditions (must have at least 2 elements)
 */
void init_default_conditions(double *y)
{
    if (y == NULL) return;
    y[0] = 1.0;  // u(0) = 1
    y[1] = 0.0;  // v(0) = 0
}

/**
 * @brief Copy solution array.
 * @param[in]  src  source array
 * @param[out] dest destination array
 */
void copy_solution(const double *src, double *dest)
{
    if (src == NULL || dest == NULL) return;
    dest[0] = src[0];
    dest[1] = src[1];
}

/**
 * @brief Check if solution satisfies energy conservation (for harmonic oscillator).
 * For the harmonic oscillator with omega=1, the energy E = u^2 + v^2 should be constant.
 * @param[in] y         solution array
 * @param[in] initial_energy expected energy (should be 1.0 for default initial conditions)
 * @param[in] tolerance maximum allowed deviation
 * @returns 1 if energy is conserved, 0 otherwise
 */
int check_energy_conservation(const double *y, double initial_energy, double tolerance)
{
    if (y == NULL) return 0;
    double current_energy = y[0] * y[0] + y[1] * y[1];
    return doubles_are_close(current_energy, initial_energy, tolerance);
}

