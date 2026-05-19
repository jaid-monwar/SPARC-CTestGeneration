/**
 * Malloc Wrapper for Testing
 *
 * Provides control over malloc/calloc/realloc failures for unit testing.
 * Compile with: gcc -Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc ...
 */

#ifndef MALLOC_WRAP_H
#define MALLOC_WRAP_H

#include <stddef.h>

/**
 * Set malloc to fail on the next N allocations.
 * After N failures, normal allocation resumes.
 *
 * Example:
 *   malloc_fail_next(1);  // Next malloc returns NULL
 *   buffer_t* buf = buffer_new(100);  // Returns NULL
 *   buffer_t* buf2 = buffer_new(100); // Works normally
 */
void malloc_fail_next(int count);

/**
 * Set malloc to fail after N successful allocations.
 * Useful for testing cleanup paths.
 *
 * Example:
 *   malloc_fail_after(2);  // First 2 mallocs succeed, 3rd fails
 */
void malloc_fail_after(int count);

/**
 * Reset malloc wrapper to normal operation.
 * Call in tearDown() to ensure clean state.
 */
void malloc_reset(void);

/**
 * Get the number of allocations made since last reset.
 */
int malloc_get_call_count(void);

#endif /* MALLOC_WRAP_H */
