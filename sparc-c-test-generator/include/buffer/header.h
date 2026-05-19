#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <ctype.h>
#include <sys/types.h>
#include "../../subjects/buffer-0.4.0/src/buffer.h"


// Function declarations
buffer_t * buffer_new(void);
buffer_t * buffer_new_with_size(size_t n);
buffer_t * buffer_new_with_string(char * str);
buffer_t * buffer_new_with_string_length(char * str, size_t len);
buffer_t * buffer_new_with_copy(char * str);
ssize_t buffer_compact(buffer_t * self);
void buffer_free(buffer_t * self);
size_t buffer_size(buffer_t * self);
size_t buffer_length(buffer_t * self);
int buffer_resize(buffer_t * self, size_t n);
int buffer_appendf(buffer_t * self, const char * format, ...);
int buffer_append(buffer_t * self, const char * str);
int buffer_append_n(buffer_t * self, const char * str, size_t len);
int buffer_prepend(buffer_t * self, char * str);
buffer_t * buffer_slice(buffer_t * buf, size_t from, ssize_t to);
int buffer_equals(buffer_t * self, buffer_t * other);
ssize_t buffer_indexof(buffer_t * self, char * str);
void buffer_trim_left(buffer_t * self);
void buffer_trim_right(buffer_t * self);
void buffer_trim(buffer_t * self);
void buffer_fill(buffer_t * self, int c);
void buffer_clear(buffer_t * self);
void buffer_print(buffer_t * self);

#endif
