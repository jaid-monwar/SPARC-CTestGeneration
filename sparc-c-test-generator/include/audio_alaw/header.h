/**
 * @file header.h
 * @brief A-law algorithm for encoding and decoding (16bit pcm <=> a-law).
 * This is the implementation of G.711 in C.
 */

#ifndef AUDIO_ALAW_H
#define AUDIO_ALAW_H

#include <inttypes.h>
#include <stddef.h>

/**
 * @brief 16bit pcm to 8bit alaw
 * @param out unsigned 8bit alaw array
 * @param in  signed 16bit pcm array
 * @param len length of pcm array
 * @returns void
 */
void encode(uint8_t *out, int16_t *in, size_t len);

/**
 * @brief 8bit alaw to 16bit pcm
 * @param out signed 16bit pcm array
 * @param in  unsigned 8bit alaw array
 * @param len length of alaw array
 * @returns void
 */
void decode(int16_t *out, uint8_t *in, size_t len);

/**
 * @brief Encode a single 16bit PCM sample to 8bit A-law
 * @param pcm_sample signed 16bit pcm value
 * @returns encoded 8bit A-law value
 */
uint8_t encode_single(int16_t pcm_sample);

/**
 * @brief Decode a single 8bit A-law sample to 16bit PCM
 * @param alaw_sample unsigned 8bit A-law value
 * @returns decoded 16bit PCM value
 */
int16_t decode_single(uint8_t alaw_sample);

/**
 * @brief Compare two PCM arrays for equality
 * @param arr1 first PCM array
 * @param arr2 second PCM array
 * @param len length of arrays
 * @returns 1 if arrays are equal, 0 otherwise
 */
int pcm_arrays_equal(int16_t *arr1, int16_t *arr2, size_t len);

/**
 * @brief Compare two A-law arrays for equality
 * @param arr1 first A-law array
 * @param arr2 second A-law array
 * @param len length of arrays
 * @returns 1 if arrays are equal, 0 otherwise
 */
int alaw_arrays_equal(uint8_t *arr1, uint8_t *arr2, size_t len);

/**
 * @brief Check if decoded PCM is within acceptable tolerance of original
 * @param original original PCM array
 * @param decoded decoded PCM array
 * @param len length of arrays
 * @param tolerance maximum allowed difference per sample
 * @returns 1 if within tolerance, 0 otherwise
 */
int pcm_within_tolerance(int16_t *original, int16_t *decoded, size_t len, int16_t tolerance);

/**
 * @brief Verify encode-decode roundtrip is within acceptable loss
 * @param pcm_input original PCM array
 * @param len length of array
 * @param tolerance maximum allowed difference per sample after roundtrip
 * @returns 1 if roundtrip is within tolerance, 0 otherwise
 */
int verify_roundtrip(int16_t *pcm_input, size_t len, int16_t tolerance);

/**
 * @brief Get the quantization level (eee bits) from an A-law sample
 * @param alaw_sample the A-law encoded sample
 * @returns quantization level (0-7)
 */
int get_quantization_level(uint8_t alaw_sample);

/**
 * @brief Get the sign bit from an A-law sample
 * @param alaw_sample the A-law encoded sample
 * @returns 1 if negative, 0 if positive
 */
int get_alaw_sign(uint8_t alaw_sample);

/**
 * @brief Get the mantissa (abcd bits) from an A-law sample
 * @param alaw_sample the A-law encoded sample
 * @returns mantissa value (0-15)
 */
int get_alaw_mantissa(uint8_t alaw_sample);

#endif /* AUDIO_ALAW_H */
