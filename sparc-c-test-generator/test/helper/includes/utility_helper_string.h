#ifndef UTILITY_HELPER_CHAR_H
#define UTILITY_HELPER_CHAR_H

#include <stddef.h>

/* String utility functions */
char* init_test_string(const char *initial_value);
char* create_test_string_buffer(size_t size);
void reset_test_string(char *string, size_t max_size);
void cleanup_test_string(char *string);

/* Character utility functions */
char init_test_char(char initial_value);
char* create_char_array(size_t size, char fill_char);

#endif /* UTILITY_HELPER_CHAR_H */
