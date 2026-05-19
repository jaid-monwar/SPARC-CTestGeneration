#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include "../../subjects/quadtree-0.1.0/src/quadtree.h"

#include <stdio.h>
#include <stdlib.h>

// Function declarations
quadtree_t * quadtree_new(double minx, double miny, double maxx, double maxy);
int quadtree_insert(quadtree_t * tree, double x, double y, void * key);
quadtree_point_t * quadtree_search(quadtree_t * tree, double x, double y);
void quadtree_free(quadtree_t * tree);
void quadtree_walk(quadtree_node_t * root, void (*descent)(quadtree_node_t *), void (*ascent)(quadtree_node_t *));

#endif
