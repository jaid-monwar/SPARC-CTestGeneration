#ifndef ASSERT_HELPER_STRING_H
#define ASSERT_HELPER_STRING_H

#include <stddef.h>

/* String assertion functions */
void assert_string_equal(const char *actual, const char *expected);
void assert_string_not_equal(const char *actual, const char *expected);
void assert_string_contains(const char *haystack, const char *needle);
void assert_string_starts_with(const char *string, const char *prefix);
void assert_string_ends_with(const char *string, const char *suffix);
void assert_string_length(const char *string, size_t expected_length);
void assert_string_empty(const char *string);
void assert_string_not_empty(const char *string);

/* Character assertion functions */
void assert_char_equal(char actual, char expected);
void assert_char_in_range(char actual, char min_char, char max_char);

#endif /* ASSERT_HELPER_STRING_H */
