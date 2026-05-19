/*
 * Algorithm : Bucket Sort
 * Time-Complexity : O(n)
 */
#ifndef SORTING_BUCKET_SORT_H
#define SORTING_BUCKET_SORT_H

#include <stdlib.h>

#define NARRAY 8    /* array size */
#define NBUCKET 5   /* bucket size */
#define INTERVAL 10 /* bucket range */

struct Node
{
    int data;
    struct Node *next;
};

/* Core sorting functions */
void BucketSort(int arr[]);
void BucketSortN(int arr[], int n, int nbucket, int interval);
struct Node *InsertionSort(struct Node *list);
int getBucketIndex(int value);
int getBucketIndexSafe(int value, int interval, int nbucket);

/* Utility functions for testing */
struct Node *createNode(int data);
void freeList(struct Node *list);
int countNodes(struct Node *list);
int isListSorted(struct Node *list);
int *copyArray(int arr[], int n);
int isArraySorted(int arr[], int n);
int arraysEqual(int arr1[], int arr2[], int n);
int arrayToString(int arr[], int n, char *buffer, int bufsize);
int listToString(struct Node *list, char *buffer, int bufsize);

#endif /* SORTING_BUCKET_SORT_H */
