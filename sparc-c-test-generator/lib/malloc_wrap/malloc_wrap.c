/**
 * Malloc Wrapper Implementation
 *
 * Compile with: gcc -Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc ...
 */

#include "malloc_wrap.h"
#include <stdlib.h>
#include <string.h>

/* Real functions provided by linker */
extern void* __real_malloc(size_t size);
extern void* __real_calloc(size_t nmemb, size_t size);
extern void* __real_realloc(void* ptr, size_t size);

/* Control state */
static int fail_countdown = 0;      /* Fail next N allocations */
static int succeed_countdown = -1;  /* Succeed N times, then fail (-1 = disabled) */
static int call_count = 0;          /* Total allocations since reset */

void malloc_fail_next(int count) {
    fail_countdown = count;
    succeed_countdown = -1;
}

void malloc_fail_after(int count) {
    succeed_countdown = count;
    fail_countdown = 0;
}

void malloc_reset(void) {
    fail_countdown = 0;
    succeed_countdown = -1;
    call_count = 0;
}

int malloc_get_call_count(void) {
    return call_count;
}

/* Check if this allocation should fail */
static int should_fail(void) {
    if (fail_countdown > 0) {
        fail_countdown--;
        return 1;
    }
    if (succeed_countdown >= 0) {
        if (succeed_countdown == 0) {
            return 1;
        }
        succeed_countdown--;
    }
    return 0;
}

void* __wrap_malloc(size_t size) {
    call_count++;
    if (should_fail()) {
        return NULL;
    }
    return __real_malloc(size);
}

void* __wrap_calloc(size_t nmemb, size_t size) {
    call_count++;
    if (should_fail()) {
        return NULL;
    }
    return __real_calloc(nmemb, size);
}

void* __wrap_realloc(void* ptr, size_t size) {
    call_count++;
    if (should_fail()) {
        return NULL;
    }
    return __real_realloc(ptr, size);
}
