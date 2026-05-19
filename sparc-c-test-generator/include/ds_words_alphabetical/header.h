/**
 * @file header.h
 * @brief Header file for the words alphabetical (word frequency counter) implementation.
 */
#ifndef DS_WORDS_ALPHABETICAL_H
#define DS_WORDS_ALPHABETICAL_H

#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/**
 * @brief structure defining a node in the binary tree
 */
struct Node
{
    char *word;          /**< the word (value) of the node */
    uint64_t frequency;  /**< number of occurrences of the word */
    struct Node *left;   /**< pointer to the left child node */
    struct Node *right;  /**< pointer to the right child node */
};

/// Global word counter for file writing (resettable for testing)
extern uint64_t g_wordCounter;

/**
 * @brief Prints error message to stderr
 * @param errorMessage the error message to be printed
 * @returns -1 to indicate error
 */
int endProgramAbruptly(char *errorMessage);

/**
 * @brief Frees memory when program is terminating
 * @param node pointer to current node
 * @returns void
 */
void freeTreeMemory(struct Node *node);

/**
 * @brief Stores word in memory
 * @param word word to be stored in memory
 * @returns a pointer to the newly allocated word if the word IS stored successfully
 * @returns NULL if the word is NOT stored
 */
char *getPointerToWord(char *word);

/**
 * @brief Closes the file after reading or writing
 * @param file pointer to the file to be closed
 * @returns 0 on success, -1 on failure
 */
int closeFile(FILE *file);

/**
 * @brief Reserves memory for new node
 * @returns a pointer to the newly allocated node if memory IS successfully reserved
 * @returns NULL if memory is NOT reserved
 */
struct Node *allocateMemoryForNode(void);

/**
 * @brief Resets the word counter used by writeContentOfTreeToFile
 * @returns void
 */
void resetWordCounter(void);

/**
 * @brief Writes contents of tree to another file alphabetically
 * @param node pointer to current node
 * @param file pointer to file
 * @returns void
 */
void writeContentOfTreeToFile(struct Node *node, FILE *file);

/**
 * @brief Adds word (node) to the correct position in tree
 * @param word word to be inserted in to the tree
 * @param currentNode node which is being compared
 * @returns a pointer to the root node
 */
struct Node *addWordToTree(char *word, struct Node *currentNode);

/**
 * @brief Reads words from file to tree
 * @param file file to be read from
 * @param root root node of tree
 * @returns a pointer to the root node
 */
struct Node *readWordsInFileToTree(FILE *file, struct Node *root);

#endif /* DS_WORDS_ALPHABETICAL_H */
