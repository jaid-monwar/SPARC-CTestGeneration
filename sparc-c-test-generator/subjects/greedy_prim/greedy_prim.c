/**
 * @file
 * @author [Timothy Maloney](https://github.com/sl1mb0)
 * @brief [Prim's algorithm](https://en.wikipedia.org/wiki/Prim%27s_algorithm)
 * implementation in C to find the MST of a weighted, connected graph.
 * @details Prim's algorithm uses a greedy approach to generate the MST of a weighted connected graph.
 * The algorithm begins at an arbitrary vertex v, and selects a next vertex u,
 * where v and u are connected by a weighted edge whose weight is the minimum of all edges connected to v.
 * @references Page 319 "Introduction to the Design and Analysis of Algorithms" - Anany Levitin
 */

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
uint16_t minimum(uint16_t arr[], uint16_t N)
{
    uint16_t index = 0;
    uint16_t min = INF;

    for (uint16_t i = 0; i < N; i++)
    {
        if (arr[i] < min)
        {
            min = arr[i];
            index = i;
        }
    }
    return index;
}

/**
 * @brief Computes the MST of a weighted, connected graph using Prim's algorithm
 * @param G adjacency matrix of the weighted graph (input)
 * @param MST adjacency matrix to store the minimum spanning tree (output)
 * @param V number of vertices in the graph
 * @returns void
 */
void prim(uint16_t G[][MAX], uint16_t MST[][MAX], uint16_t V)
{
    uint16_t u, v;
    uint16_t E_t[MAX], path[MAX];
    uint16_t V_t[MAX], no_of_edges;

    if (V == 0 || V > MAX)
    {
        return;
    }

    E_t[0] = 0;  // edges for current vertex
    V_t[0] = 1;  // list of visited vertices

    for (uint16_t i = 1; i < V; i++)
    {
        E_t[i] = G[i][0];
        path[i] = 0;
        V_t[i] = 0;
    }

    no_of_edges = V - 1;

    while (no_of_edges > 0)
    {
        u = minimum(E_t, V);
        while (V_t[u] == 1)
        {
            E_t[u] = INF;
            u = minimum(E_t, V);
        }

        v = path[u];
        MST[v][u] = E_t[u];
        MST[u][v] = E_t[u];
        no_of_edges--;
        V_t[u] = 1;

        for (uint16_t i = 1; i < V; i++)
        {
            if (V_t[i] == 0 && G[u][i] < E_t[i])
            {
                E_t[i] = G[u][i];
                path[i] = u;
            }
        }
    }
}

/**
 * @brief Initializes a matrix to all zeros
 * @param matrix the matrix to initialize
 * @param size the dimension of the square matrix
 * @returns void
 */
void init_matrix(uint16_t matrix[][MAX], uint16_t size)
{
    for (uint16_t i = 0; i < size; i++)
    {
        for (uint16_t j = 0; j < size; j++)
        {
            matrix[i][j] = 0;
        }
    }
}

/**
 * @brief Copies values from a source array to a graph matrix
 * @param G destination adjacency matrix
 * @param values source 1D array (row-major order)
 * @param V number of vertices
 * @returns void
 */
void set_graph_from_array(uint16_t G[][MAX], uint16_t *values, uint16_t V)
{
    for (uint16_t i = 0; i < V; i++)
    {
        for (uint16_t j = 0; j < V; j++)
        {
            G[i][j] = values[i * V + j];
        }
    }
}

/**
 * @brief Computes the total weight of edges in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @returns total weight of the MST (each edge counted once)
 */
uint32_t mst_total_weight(uint16_t MST[][MAX], uint16_t V)
{
    uint32_t total = 0;
    for (uint16_t i = 0; i < V; i++)
    {
        for (uint16_t j = i + 1; j < V; j++)
        {
            total += MST[i][j];
        }
    }
    return total;
}

/**
 * @brief Counts the number of edges in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @returns number of edges in the MST
 */
uint16_t mst_edge_count(uint16_t MST[][MAX], uint16_t V)
{
    uint16_t count = 0;
    for (uint16_t i = 0; i < V; i++)
    {
        for (uint16_t j = i + 1; j < V; j++)
        {
            if (MST[i][j] > 0)
            {
                count++;
            }
        }
    }
    return count;
}

/**
 * @brief Checks if two matrices are equal
 * @param A first matrix
 * @param B second matrix
 * @param V dimension of the square matrices
 * @returns 1 if matrices are equal, 0 otherwise
 */
int matrices_equal(uint16_t A[][MAX], uint16_t B[][MAX], uint16_t V)
{
    for (uint16_t i = 0; i < V; i++)
    {
        for (uint16_t j = 0; j < V; j++)
        {
            if (A[i][j] != B[i][j])
            {
                return 0;
            }
        }
    }
    return 1;
}

/**
 * @brief Checks if a vertex is connected in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @param vertex the vertex to check
 * @returns 1 if vertex has at least one edge, 0 otherwise
 */
int vertex_is_connected(uint16_t MST[][MAX], uint16_t V, uint16_t vertex)
{
    if (vertex >= V)
    {
        return 0;
    }
    for (uint16_t j = 0; j < V; j++)
    {
        if (MST[vertex][j] > 0)
        {
            return 1;
        }
    }
    return 0;
}

/**
 * @brief Gets the edge weight between two vertices in the MST
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @param u first vertex
 * @param v second vertex
 * @returns edge weight, or 0 if no edge exists
 */
uint16_t get_edge_weight(uint16_t MST[][MAX], uint16_t V, uint16_t u, uint16_t v)
{
    if (u >= V || v >= V)
    {
        return 0;
    }
    return MST[u][v];
}

/**
 * @brief Writes the MST to a string buffer for testing
 * @param MST adjacency matrix of the MST
 * @param V number of vertices
 * @param buffer output buffer (must be large enough)
 * @param buffer_size size of the output buffer
 * @returns number of characters written, or -1 on error
 */
int mst_to_string(uint16_t MST[][MAX], uint16_t V, char *buffer, size_t buffer_size)
{
    if (buffer == NULL || buffer_size == 0)
    {
        return -1;
    }

    size_t offset = 0;
    for (uint16_t i = 0; i < V && offset < buffer_size - 1; i++)
    {
        for (uint16_t j = 0; j < V && offset < buffer_size - 1; j++)
        {
            int written = snprintf(buffer + offset, buffer_size - offset, "%u ", MST[i][j]);
            if (written < 0)
            {
                return -1;
            }
            offset += (size_t)written;
        }
        if (offset < buffer_size - 1)
        {
            buffer[offset++] = '\n';
        }
    }
    buffer[offset] = '\0';
    return (int)offset;
}
