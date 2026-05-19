/**
 * \file
 * \brief Compute statistics for data entered in real-time
 * \author [Krishna Vedala](https://github.com/kvedala)
 *
 * This algorithm is really beneficial to compute statistics on data read in
 * realtime. For example, devices reading biometrics data. The algorithm is
 * simple enough to be easily implemented in an embedded system.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Static state for stats_computer1 */
static unsigned int sc1_n = 0;
static float sc1_Ex = 0.f, sc1_Ex2 = 0.f;
static float sc1_K = 0.f;

/* Static state for stats_computer2 */
static unsigned int sc2_n = 0;
static float sc2_mu = 0.f, sc2_M = 0.f;

/**
 * Reset the internal state of stats_computer1.
 * Must be called before starting a new data set.
 */
void stats_computer1_reset(void)
{
    sc1_n = 0;
    sc1_Ex = 0.f;
    sc1_Ex2 = 0.f;
    sc1_K = 0.f;
}

/**
 * Reset the internal state of stats_computer2.
 * Must be called before starting a new data set.
 */
void stats_computer2_reset(void)
{
    sc2_n = 0;
    sc2_mu = 0.f;
    sc2_M = 0.f;
}

/**
 * Get the current sample count for stats_computer1.
 * \return Number of samples processed
 */
unsigned int stats_computer1_get_count(void)
{
    return sc1_n;
}

/**
 * Get the current sample count for stats_computer2.
 * \return Number of samples processed
 */
unsigned int stats_computer2_get_count(void)
{
    return sc2_n;
}

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
void stats_computer1(float x, float *mean, float *variance, float *std)
{
    if (sc1_n == 0)
        sc1_K = x;
    sc1_n++;
    float tmp = x - sc1_K;
    sc1_Ex += tmp;
    sc1_Ex2 += tmp * tmp;

    /* return sample mean computed till last sample */
    if (mean != NULL)
        *mean = sc1_K + sc1_Ex / sc1_n;

    /* return data variance computed till last sample */
    if (variance != NULL)
    {
        if (sc1_n > 1)
            *variance = (sc1_Ex2 - (sc1_Ex * sc1_Ex) / sc1_n) / (sc1_n - 1);
        else
            *variance = 0.f;  /* variance undefined for single sample */
    }

    /* return sample standard deviation computed till last sample */
    if (std != NULL)
    {
        if (variance != NULL)
            *std = sqrtf(*variance);
        else
        {
            float var;
            if (sc1_n > 1)
                var = (sc1_Ex2 - (sc1_Ex * sc1_Ex) / sc1_n) / (sc1_n - 1);
            else
                var = 0.f;
            *std = sqrtf(var);
        }
    }
}

/**
 * continuous mean and variance computation using
 * Welford's algorithm (very accurate)
 * \param[in] x new value added to data set
 * \param[out] mean if not NULL, mean returns mean of data set
 * \param[out] variance if not NULL, variance returns variance of data set
 * \param[out] std if not NULL, std returns standard deviation of data set
 */
void stats_computer2(float x, float *mean, float *variance, float *std)
{
    sc2_n++;
    float delta = x - sc2_mu;
    sc2_mu += delta / sc2_n;
    float delta2 = x - sc2_mu;
    sc2_M += delta * delta2;

    /* return sample mean computed till last sample */
    if (mean != NULL)
        *mean = sc2_mu;

    /* return data variance computed till last sample */
    if (variance != NULL)
    {
        if (sc2_n > 0)
            *variance = sc2_M / sc2_n;
        else
            *variance = 0.f;
    }

    /* return sample standard deviation computed till last sample */
    if (std != NULL)
    {
        if (variance != NULL)
            *std = sqrtf(*variance);
        else
        {
            float var = (sc2_n > 0) ? sc2_M / sc2_n : 0.f;
            *std = sqrtf(var);
        }
    }
}

/**
 * Compute mean of an array using standard method (for verification).
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \return mean value
 */
float compute_reference_mean(const float *data, int n)
{
    if (data == NULL || n <= 0)
        return 0.f;

    float sum = 0.f;
    for (int i = 0; i < n; i++)
        sum += data[i];
    return sum / n;
}

/**
 * Compute population variance of an array using standard method (for verification).
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \return population variance
 */
float compute_reference_variance(const float *data, int n)
{
    if (data == NULL || n <= 0)
        return 0.f;

    float mean = compute_reference_mean(data, n);
    float sum_sq = 0.f;
    for (int i = 0; i < n; i++)
    {
        float diff = data[i] - mean;
        sum_sq += diff * diff;
    }
    return sum_sq / n;
}

/**
 * Compute standard deviation from variance.
 * \param[in] variance the variance value
 * \return standard deviation
 */
float compute_std_from_variance(float variance)
{
    if (variance < 0.f)
        return 0.f;
    return sqrtf(variance);
}

/**
 * Check if two floats are approximately equal within a tolerance.
 * \param[in] a first value
 * \param[in] b second value
 * \param[in] tolerance maximum allowed difference
 * \return 1 if approximately equal, 0 otherwise
 */
int float_approx_equal(float a, float b, float tolerance)
{
    return fabsf(a - b) < tolerance;
}

/**
 * Process an array of samples through stats_computer1.
 * Resets state before processing.
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \param[out] mean final mean value (can be NULL)
 * \param[out] variance final variance value (can be NULL)
 * \param[out] std final standard deviation (can be NULL)
 */
void process_samples_method1(const float *data, int n, float *mean, float *variance, float *std)
{
    stats_computer1_reset();
    if (data == NULL || n <= 0)
    {
        if (mean != NULL) *mean = 0.f;
        if (variance != NULL) *variance = 0.f;
        if (std != NULL) *std = 0.f;
        return;
    }

    for (int i = 0; i < n; i++)
        stats_computer1(data[i], mean, variance, std);
}

/**
 * Process an array of samples through stats_computer2.
 * Resets state before processing.
 * \param[in] data array of float values
 * \param[in] n number of elements
 * \param[out] mean final mean value (can be NULL)
 * \param[out] variance final variance value (can be NULL)
 * \param[out] std final standard deviation (can be NULL)
 */
void process_samples_method2(const float *data, int n, float *mean, float *variance, float *std)
{
    stats_computer2_reset();
    if (data == NULL || n <= 0)
    {
        if (mean != NULL) *mean = 0.f;
        if (variance != NULL) *variance = 0.f;
        if (std != NULL) *std = 0.f;
        return;
    }

    for (int i = 0; i < n; i++)
        stats_computer2(data[i], mean, variance, std);
}
