/**
 * @file header.h
 * @brief Header file for the affine cipher implementation
 */

#ifndef CIPHER_AFFINE_H
#define CIPHER_AFFINE_H

#include <stdlib.h>
#include <string.h>

/**
 * @brief number of characters in our alphabet (printable ASCII characters)
 */
#define ALPHABET_SIZE 95

/**
 * @brief used to convert a printable byte (32 to 126) to an element of the
 * group Z_95 (0 to 94)
 */
#define Z95_CONVERSION_CONSTANT 32

/**
 * @brief a structure representing an affine cipher key
 */
typedef struct
{
    int a;  ///< what the character is being multiplied by
    int b;  ///< what is being added after the multiplication with `a`
} affine_key_t;

/**
 * @brief finds the value x such that (a * x) % m = 1
 *
 * @param a number we are finding the inverse for
 * @param m the modulus the inversion is based on
 *
 * @returns the modular multiplicative inverse of `a` mod `m`
 */
int modular_multiplicative_inverse(unsigned int a, unsigned int m);

/**
 * @brief Given a valid affine cipher key, this function will produce the
 * inverse key.
 *
 * @param key They key to be inverted
 *
 * @returns inverse of key
 */
affine_key_t inverse_key(affine_key_t key);

/**
 * @brief Encrypts character string `s` with key (in-place)
 *
 * @param s string to be encrypted
 * @param key affine key used for encryption
 *
 * @returns void
 */
void affine_encrypt(char *s, affine_key_t key);

/**
 * @brief Decrypts an affine ciphertext (in-place)
 *
 * @param s string to be decrypted
 * @param key Key used when s was encrypted
 *
 * @returns void
 */
void affine_decrypt(char *s, affine_key_t key);

/**
 * @brief Computes the greatest common divisor of two numbers
 *
 * @param a first number
 * @param b second number
 *
 * @returns the GCD of a and b
 */
int gcd(int a, int b);

/**
 * @brief Checks if a key is valid for the affine cipher
 * A valid key requires gcd(key.a, ALPHABET_SIZE) == 1
 *
 * @param key the affine key to validate
 *
 * @returns 1 if key is valid, 0 otherwise
 */
int is_valid_key(affine_key_t key);

/**
 * @brief Creates an affine key with the given a and b values
 *
 * @param a the multiplier (must be coprime with ALPHABET_SIZE)
 * @param b the additive constant
 *
 * @returns the created affine_key_t structure
 */
affine_key_t create_key(int a, int b);

/**
 * @brief Encrypts a string and returns a newly allocated copy
 * The caller is responsible for freeing the returned string
 *
 * @param s the string to encrypt (not modified)
 * @param key the affine key for encryption
 *
 * @returns newly allocated encrypted string, or NULL on failure
 */
char *affine_encrypt_copy(const char *s, affine_key_t key);

/**
 * @brief Decrypts a string and returns a newly allocated copy
 * The caller is responsible for freeing the returned string
 *
 * @param s the string to decrypt (not modified)
 * @param key the affine key used for original encryption
 *
 * @returns newly allocated decrypted string, or NULL on failure
 */
char *affine_decrypt_copy(const char *s, affine_key_t key);

/**
 * @brief Checks if encryption followed by decryption returns original string
 *
 * @param s the original string
 * @param key the affine key to test
 *
 * @returns 1 if round-trip successful, 0 otherwise
 */
int verify_round_trip(const char *s, affine_key_t key);

/**
 * @brief Checks if a character is within the valid printable ASCII range
 *
 * @param c the character to check
 *
 * @returns 1 if valid (32-126), 0 otherwise
 */
int is_valid_char(char c);

/**
 * @brief Checks if all characters in a string are valid for affine cipher
 *
 * @param s the string to check
 *
 * @returns 1 if all characters valid, 0 otherwise
 */
int is_valid_string(const char *s);

#endif /* CIPHER_AFFINE_H */
