/**
 * @file header.h
 * @brief Header file for the circular doubly linked list implementation.
 */
#ifndef DS_CIRCULAR_DOUBLY_LINKED_LIST_H
#define DS_CIRCULAR_DOUBLY_LINKED_LIST_H

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

/**
 * @brief Circular Doubly linked list struct
 */
typedef struct node
{
    struct node *prev, *next;  /**< List pointers */
    uint64_t value;            /**< Data stored on each node */
} ListNode;

/**
 * @brief Create a list node
 * @param data the data that the node initialises with
 * @return ListNode* pointer to the newly created list node
 */
ListNode *create_node(uint64_t data);

/**
 * @brief Insert a node at start of list
 * @param head start pointer of list
 * @param data the data that the node initialises with
 * @return ListNode* pointer to the newly created list node inserted at the head
 */
ListNode *insert_at_head(ListNode *head, uint64_t data);

/**
 * @brief Insert a node at end of list
 * @param head start pointer of list
 * @param data the data that the node initialises with
 * @return ListNode* pointer to the head of list
 */
ListNode *insert_at_tail(ListNode *head, uint64_t data);

/**
 * @brief Function for deletion of the first node in list
 * @param head start pointer of list
 * @return ListNode* pointer to the list node after deleting first node
 */
ListNode *delete_from_head(ListNode *head);

/**
 * @brief Function for deletion of the last node in list
 * @param head start pointer of list
 * @return ListNode* pointer to the list node after deleting last node
 */
ListNode *delete_from_tail(ListNode *head);

/**
 * @brief The function that will return current size of list
 * @param head start pointer of list
 * @return int size of list
 */
int getsize(ListNode *head);

/**
 * @brief Display list function
 * @param head start pointer of list
 */
void display_list(ListNode *head);

/**
 * @brief Access the list by index
 * @param list pointer to the target list
 * @param index access location
 * @return uint64_t the value at the specified index
 */
uint64_t get(ListNode *list, const int index);

#endif /* DS_CIRCULAR_DOUBLY_LINKED_LIST_H */
