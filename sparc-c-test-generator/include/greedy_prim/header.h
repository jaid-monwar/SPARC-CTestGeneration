/**
 * @file header.h
 * @brief Header file for Prim's algorithm MST implementation
 */

#ifndef GREEDY_PRIM_H
#define GREEDY_PRIM_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

#define MAX 20
#define INF 999

/**
 * @brief Finds index of minimum element in edge list for an arbitrary vertex
 * @param arr graph row
 * @param N number of elements in arr
 * @returns index of minimum element in arr
 */
uint16_t minimum(uint16_t arr[], uint16_t N);

/**
 * @brief Computes the MST of a weighted, connected graph using Prim's algorithm
 * @param G adjacency matrix of the weighted graph (input)
 * @param MST adjacency matrix to store the minimum spanning tree (output)
 * @param V number of vertices in the graph
 * @returns void
 */
void prim(uint16_t G[][MAX], uint16_t MST[][MAX], uint16_t V);

/**
 * @brief Initializes a matrix to all zeros
 * @param matrix the matrix to initialize
 * @param size the dimension of the square matrix
 * @returns void
 */
void init_matrix(uint16_t matrix[][MAX], uint16_t size);

/**
 * @brief Copies values from a source array to a graph matrix
 * @param G destination adjacency matrix
 * @param values source 1D array (row-major order)
 * @param V number of vertices
 * @returns void
 */
void set_graph_from_array(uint16_t G[][MAX], uint16_t *values, uint16_t V);

/**
 * @brief Computes the total weight of edges in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @returns total weight of the MST (each edge counted once)
 */
uint32_t mst_total_weight(uint16_t MST[][MAX], uint16_t V);

/**
 * @brief Counts the number of edges in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @returns number of edges in the MST
 */
uint16_t mst_edge_count(uint16_t MST[][MAX], uint16_t V);

/**
 * @brief Checks if two matrices are equal
 * @param A first matrix
 * @param B second matrix
 * @param V dimension of the square matrices
 * @returns 1 if matrices are equal, 0 otherwise
 */
int matrices_equal(uint16_t A[][MAX], uint16_t B[][MAX], uint16_t V);

/**
 * @brief Checks if a vertex is connected in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @param vertex the vertex to check
 * @returns 1 if vertex has at least one edge, 0 otherwise
 */
int vertex_is_connected(uint16_t MST[][MAX], uint16_t V, uint16_t vertex);

/**
 * @brief Gets the edge weight between two vertices in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @param u first vertex
 * @param v second vertex
 * @returns edge weight, or 0 if no edge exists
 */
uint16_t get_edge_weight(uint16_t MST[][MAX], uint16_t V, uint16_t u, uint16_t v);

/**
 * @brief Writes the MST to a string buffer for testing
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @param buffer output buffer (must be large enough)
 * @param buffer_size size of the output buffer
 * @returns number of characters written, or -1 on error
 */
int mst_to_string(uint16_t MST[][MAX], uint16_t V, char *buffer, size_t buffer_size);

#endif /* GREEDY_PRIM_H */
