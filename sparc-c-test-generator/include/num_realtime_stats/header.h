/**
 * \file header.h
 * \brief Header file for real-time statistics computation
 */

#ifndef NUM_REALTIME_STATS_H
#define NUM_REALTIME_STATS_H

/**
 * Reset the internal state of stats_computer1.
 * Must be called before starting a new data set.
 */
void stats_computer1_reset(void);

/**
 * Reset the internal state of stats_computer2.
 * Must be called before starting a new data set.
 */
void stats_computer2_reset(void);

/**
 * Get the current sample count for stats_computer1.
 * \return Number of samples processed
 */
unsigned int stats_computer1_get_count(void);

/**
 * Get the current sample count for stats_computer2.
 * \return Number of samples processed
 */
unsigned int stats_computer2_get_count(void);

/**
 * continuous mean and variance computation using
 * first value as an approximation for the mean.
 * If the first number is much far from the mean, the algorithm becomes very
 * inaccurate to compute variance and standard deviation.
 * \param[in] x new value added to data set
 * \param[out] mean if not NULL, mean returns mean of data set
 * \param[out] variance if not NULL, variance returns variance of data set
 * \param[out] std if not NULL, std returns standard deviation of data set
 */
void stats_computer1(float x, float *mean, float *variance, float *std);

/**
 * continuous mean and variance computation using
 * Welford's algorithm (very accurate)
 * \param[in] x new value added to data set
 * \param[out] mean if not NULL, mean returns mean of data set
 * \param[out] variance if not NULL, variance returns variance of data set
 * \param[out] std if not NULL, std returns standard deviation of data set
 */
void stats_computer2(float x, float *mean, float *variance, float *std);

/**
 * Compute mean of an array using standard method (for verification).
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \return mean value
 */
float compute_reference_mean(const float *data, int n);

/**
 * Compute population variance of an array using standard method (for verification).
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \return population variance
 */
float compute_reference_variance(const float *data, int n);

/**
 * Compute standard deviation from variance.
 * \param[in] variance the variance value
 * \return standard deviation
 */
float compute_std_from_variance(float variance);

/**
 * Check if two floats are approximately equal within a tolerance.
 * \param[in] a first value
 * \param[in] b second value
 * \param[in] tolerance maximum allowed difference
 * \return 1 if approximately equal, 0 otherwise
 */
int float_approx_equal(float a, float b, float tolerance);

/**
 * Process an array of samples through stats_computer1.
 * Resets state before processing.
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \param[out] mean final mean value (can be NULL)
 * \param[out] variance final variance value (can be NULL)
 * \param[out] std final standard deviation (can be NULL)
 */
void process_samples_method1(const float *data, int n, float *mean, float *variance, float *std);

/**
 * Process an array of samples through stats_computer2.
 * Resets state before processing.
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \param[out] mean final mean value (can be NULL)
 * \param[out] variance final variance value (can be NULL)
 * \param[out] std final standard deviation (can be NULL)
 */
void process_samples_method2(const float *data, int n, float *mean, float *variance, float *std);

#endif /* NUM_REALTIME_STATS_H */
