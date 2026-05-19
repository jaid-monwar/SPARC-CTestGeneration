#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../subjects/rgba/src/rgba.h"


// Function declarations
rgba_t rgba_new(uint32_t rgba);
void rgba_to_string(rgba_t rgba, char * buf, size_t len);
uint32_t rgba_from_string(const char * str, short * ok);
void rgba_inspect(uint32_t rgba);

#endif
