#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <float.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>


// Struct definitions
typedef struct observation {
    double x;
    double y;
    int group;
} observation;

typedef struct cluster {
    double x;
    double y;
    size_t count;
} cluster;

// Macros
#define _USE_MATH_DEFINES
// Function declarations
int calculateNearst(observation * o, cluster clusters[], int k);
void calculateCentroid(observation observations[], size_t size, cluster * centroid);
cluster * kMeans(observation observations[], size_t size, int k);
void printEPS(observation pts[], size_t len, cluster cent[], int k);

#endif
