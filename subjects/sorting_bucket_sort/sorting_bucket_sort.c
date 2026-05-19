/*
 * Algorithm : Bucket Sort
 * Time-Complexity : O(n)
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NARRAY 8    /* array size */
#define NBUCKET 5   /* bucket size */
#define INTERVAL 10 /* bucket range */

struct Node
{
    int data;
    struct Node *next;
};

/* Forward declarations */
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

void BucketSort(int arr[])
{
    BucketSortN(arr, NARRAY, NBUCKET, INTERVAL);
}

/* Parameterized version for flexible testing */
void BucketSortN(int arr[], int n, int nbucket, int interval)
{
    int i, j;
    struct Node **buckets;

    if (arr == NULL || n <= 0 || nbucket <= 0 || interval <= 0)
    {
        return;
    }

    /* allocate memory for array of pointers to the buckets */
    buckets = (struct Node **)malloc(sizeof(struct Node *) * nbucket);
    if (buckets == NULL)
    {
        return;
    }

    /* initialize pointers to the buckets */
    for (i = 0; i < nbucket; ++i)
    {
        buckets[i] = NULL;
    }

    /* put items into the buckets */
    /* creates a link list in each bucket slot */
    for (i = 0; i < n; ++i)
    {
        struct Node *current;
        int pos = getBucketIndexSafe(arr[i], interval, nbucket);
        current = (struct Node *)malloc(sizeof(struct Node));
        if (current == NULL)
        {
            /* cleanup on allocation failure */
            for (j = 0; j < nbucket; ++j)
            {
                freeList(buckets[j]);
            }
            free(buckets);
            return;
        }
        current->data = arr[i];
        current->next = buckets[pos];
        buckets[pos] = current;
    }

    /* sorting bucket using Insertion Sort */
    for (i = 0; i < nbucket; ++i)
    {
        buckets[i] = InsertionSort(buckets[i]);
    }

    /* put items back to original array */
    for (j = 0, i = 0; i < nbucket; ++i)
    {
        struct Node *node;
        node = buckets[i];
        while (node)
        {
            /* precondition for avoiding out of bounds by the array */
            if (j >= n)
            {
                break;
            }
            arr[j++] = node->data;
            node = node->next;
        }
    }

    /* free memory */
    for (i = 0; i < nbucket; ++i)
    {
        freeList(buckets[i]);
    }
    free(buckets);
}

/* Insertion Sort */
struct Node *InsertionSort(struct Node *list)
{
    struct Node *k, *nodeList;
    /* need at least two items to sort */
    if (list == NULL || list->next == NULL)
    {
        return list;
    }

    nodeList = list;
    k = list->next;
    nodeList->next = NULL; /* 1st node is new list */
    while (k != NULL)
    {
        struct Node *ptr;
        /* check if insert before first */
        if (nodeList->data > k->data)
        {
            struct Node *tmp;
            tmp = k;
            k = k->next;  /* important for the while */
            tmp->next = nodeList;
            nodeList = tmp;
            continue;
        }

        /* from begin up to end */
        /* finds [i] > [i+1] */
        for (ptr = nodeList; ptr->next != NULL; ptr = ptr->next)
        {
            if (ptr->next->data > k->data)
                break;
        }

        /* if found (above) */
        if (ptr->next != NULL)
        {
            struct Node *tmp;
            tmp = k;
            k = k->next;  /* important for the while */
            tmp->next = ptr->next;
            ptr->next = tmp;
            continue;
        }
        else
        {
            ptr->next = k;
            k = k->next;  /* important for the while */
            ptr->next->next = NULL;
            continue;
        }
    }
    return nodeList;
}

/* Original getBucketIndex - can return negative for negative values */
int getBucketIndex(int value)
{
    return value / INTERVAL;
}

/* Safe version that clamps to valid bucket range */
int getBucketIndexSafe(int value, int interval, int nbucket)
{
    int index;
    if (interval <= 0 || nbucket <= 0)
    {
        return 0;
    }
    index = value / interval;
    if (index < 0)
    {
        return 0;
    }
    if (index >= nbucket)
    {
        return nbucket - 1;
    }
    return index;
}

/* ============================================
 * Utility functions for testing
 * ============================================ */

/* Create a new node with the given data */
struct Node *createNode(int data)
{
    struct Node *node = (struct Node *)malloc(sizeof(struct Node));
    if (node != NULL)
    {
        node->data = data;
        node->next = NULL;
    }
    return node;
}

/* Free all nodes in a linked list */
void freeList(struct Node *list)
{
    struct Node *current = list;
    while (current != NULL)
    {
        struct Node *tmp = current;
        current = current->next;
        free(tmp);
    }
}

/* Count the number of nodes in a linked list */
int countNodes(struct Node *list)
{
    int count = 0;
    struct Node *current = list;
    while (current != NULL)
    {
        count++;
        current = current->next;
    }
    return count;
}

/* Check if a linked list is sorted in ascending order */
int isListSorted(struct Node *list)
{
    if (list == NULL || list->next == NULL)
    {
        return 1;  /* empty or single element is sorted */
    }
    struct Node *current = list;
    while (current->next != NULL)
    {
        if (current->data > current->next->data)
        {
            return 0;  /* not sorted */
        }
        current = current->next;
    }
    return 1;  /* sorted */
}

/* Create a copy of an array */
int *copyArray(int arr[], int n)
{
    if (arr == NULL || n <= 0)
    {
        return NULL;
    }
    int *copy = (int *)malloc(sizeof(int) * n);
    if (copy != NULL)
    {
        memcpy(copy, arr, sizeof(int) * n);
    }
    return copy;
}

/* Check if an array is sorted in ascending order */
int isArraySorted(int arr[], int n)
{
    if (arr == NULL || n <= 1)
    {
        return 1;  /* null, empty, or single element is sorted */
    }
    for (int i = 0; i < n - 1; i++)
    {
        if (arr[i] > arr[i + 1])
        {
            return 0;  /* not sorted */
        }
    }
    return 1;  /* sorted */
}

/* Check if two arrays are equal */
int arraysEqual(int arr1[], int arr2[], int n)
{
    if (arr1 == NULL && arr2 == NULL)
    {
        return 1;
    }
    if (arr1 == NULL || arr2 == NULL)
    {
        return 0;
    }
    for (int i = 0; i < n; i++)
    {
        if (arr1[i] != arr2[i])
        {
            return 0;
        }
    }
    return 1;
}

/* Convert array to string representation */
int arrayToString(int arr[], int n, char *buffer, int bufsize)
{
    if (buffer == NULL || bufsize <= 0)
    {
        return -1;
    }
    buffer[0] = '\0';
    if (arr == NULL || n <= 0)
    {
        snprintf(buffer, bufsize, "[]");
        return 0;
    }
    int offset = 0;
    offset += snprintf(buffer + offset, bufsize - offset, "[");
    for (int i = 0; i < n && offset < bufsize - 1; i++)
    {
        if (i > 0)
        {
            offset += snprintf(buffer + offset, bufsize - offset, ", ");
        }
        offset += snprintf(buffer + offset, bufsize - offset, "%d", arr[i]);
    }
    if (offset < bufsize - 1)
    {
        snprintf(buffer + offset, bufsize - offset, "]");
    }
    return 0;
}

/* Convert linked list to string representation */
int listToString(struct Node *list, char *buffer, int bufsize)
{
    if (buffer == NULL || bufsize <= 0)
    {
        return -1;
    }
    buffer[0] = '\0';
    if (list == NULL)
    {
        snprintf(buffer, bufsize, "[]");
        return 0;
    }
    int offset = 0;
    offset += snprintf(buffer + offset, bufsize - offset, "[");
    struct Node *current = list;
    int first = 1;
    while (current != NULL && offset < bufsize - 1)
    {
        if (!first)
        {
            offset += snprintf(buffer + offset, bufsize - offset, ", ");
        }
        first = 0;
        offset += snprintf(buffer + offset, bufsize - offset, "%d", current->data);
        current = current->next;
    }
    if (offset < bufsize - 1)
    {
        snprintf(buffer + offset, bufsize - offset, "]");
    }
    return 0;
}
