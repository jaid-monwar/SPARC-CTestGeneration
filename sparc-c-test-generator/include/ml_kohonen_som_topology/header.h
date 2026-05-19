#ifndef ML_KOHONEN_SOM_TOPOLOGY_HEADER_H
#define ML_KOHONEN_SOM_TOPOLOGY_HEADER_H

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifndef max
#define max(a, b) (((a) > (b)) ? (a) : (b))
#endif
#ifndef min
#define min(a, b) (((a) < (b)) ? (a) : (b))
#endif

struct kohonen_array_3d {
    int dim1;
    int dim2;
    int dim3;
    double *data;
};

// Function declarations
double *kohonen_data_3d(const struct kohonen_array_3d *arr, int x, int y, int z);
double kohonen_random(double a, double b);
int save_2d_data(const char *fname, double **X, int num_points, int num_features);
int save_u_matrix(const char *fname, struct kohonen_array_3d *W);
void get_min_2d(double **X, int N, double *val, int *x_idx, int *y_idx);
double kohonen_update_weights(const double *X, struct kohonen_array_3d *W,
                              double **D, int num_out, int num_features,
                              double alpha, int R);
void kohonen_som(double **X, struct kohonen_array_3d *W, int num_samples,
                 int num_features, int num_out, double alpha_min);
double get_clock_diff(clock_t start_t, clock_t end_t);

#endif
