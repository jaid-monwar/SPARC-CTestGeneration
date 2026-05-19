#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/signal.h>
// #include "../../subjects/xzoom/test/x11_mock.h"
#include <sys/time.h>
#include <unistd.h>
// #include "../../subjects/xzoom/scale.h"


// Macros
#define SRC
#define DST
#define WIDTH
#define HEIGHT
#define MAG
#define MAGX
#define MAGY
#define NDELAYS
#define T
#define T
#define T
// Function declarations
void timeout_func(int signum);
void allocate_images(void);
void destroy_images(void);
void Usage(void);
void resize(int new_width, int new_height);
void scale8(void);
void scale16(void);
void scale32(void);
void xzoom(int buttonpressed);
int xzoom_main(int argc, char * * argv);

#endif
