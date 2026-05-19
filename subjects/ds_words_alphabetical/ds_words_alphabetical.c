/**
 * @file
 * @brief Printing the [words contained in a
 * file](http://www.dailyfreecode.com/Code/word-list-reads-text-file-makes-2050.aspx)
 * named `file.txt` in alphabetical order and also their frequencies in to
 * another file "wordcount.txt"
 * @details
 * Given a file (`file.txt`) containing words (like a publication or a novel),
 * where words are separated by a space, newline, or underscore.
 * This program prints (writes or outputs) to another file (`wordcount.txt`),
 * the individual words contained in 'file.txt' with their frequencies (number
 * of occurrences) each on a newline and in alphabetical order. This program uses
 * the binary tree data structure to accomplish this task.
 * @author [Randy Kwalar](https://github.com/RandyKdev)
 */

#include <assert.h>    /// for assert
#include <ctype.h>     /// for type checks
#include <inttypes.h>  /// for uint64_t based types, int64_t based types
#include <stdbool.h>   /// for boolean data type
#include <stdio.h>     /// for IO operations
#include <stdlib.h>    /// for memory allocation
#include <string.h>    /// for string operations

/**
 * @brief structure defining a node in the binary tree
 */
struct Node
{
    char *word;          ///< the word (value) of the node
    uint64_t frequency;  ///< number of occurrences of the word
    struct Node *left;   ///< pointer to the left child node
    struct Node *right;  ///< pointer to the right child node
};

/**
 * @brief Prints error message to stderr
 * @param errorMessage the error message to be printed
 * @returns -1 to indicate error
 */
int endProgramAbruptly(char *errorMessage)
{
    fprintf(stderr, "%s\n", errorMessage);
    return -1;
}

/**
 * @brief Frees memory when program is terminating
 * @param node pointer to current node
 * @returns void
 */
void freeTreeMemory(struct Node *node)
{
    if (node != NULL)
    {
        freeTreeMemory(node->left);
        freeTreeMemory(node->right);
        free(node->word);  // freeing node->word because memory was allocated
                           // using malloc
        free(node);  // freeing node because memory was allocated using malloc
    }
}

/**
 * @brief Stores word in memory
 * @param word word to be stored in memory
 * @returns a pointer to the newly allocated word if the word IS stored successfully
 * @returns `NULL` if the word is NOT stored
 */
char *getPointerToWord(char *word)
{
    char *string =
        (char *)malloc((strlen(word) + 1) * sizeof(char));  ///< pointer to string
    // + 1 is for the '\0' character
    if (string != NULL)
    {
        strcpy(string, word);
        return string;
    }
    endProgramAbruptly(
        "\nA problem occurred while reserving memory for the word\n");
    return NULL;  // returns NULL on allocation failure
}

/**
 * @brief Closes the file after reading or writing
 * @param file pointer to the file to be closed
 * @returns 0 on success, -1 on failure
 */
int closeFile(FILE *file)
{
    if (fclose(file)) {
        return endProgramAbruptly("\nA Problem Occurred while closing a file\n");
    }
    return 0;
}

/**
 * @brief Reserves memory for new node
 * @returns a pointer to the newly allocated node if memory IS successfully reserved
 * @returns `NULL` if memory is NOT reserved
 */
struct Node *allocateMemoryForNode()
{
    struct Node *node =
        (struct Node *)malloc(sizeof(struct Node));  ///< pointer to the node
    if (node != NULL)
    {
        return node;
    }
    endProgramAbruptly(
        "\nA problem occurred while reserving memory for the structure\n");
    return NULL;  // returns NULL on allocation failure
}

/**
 * @brief Counts the total number of nodes in the tree
 * @param node pointer to current node
 * @returns the number of nodes in the tree
 */
uint64_t countNodes(struct Node *node)
{
    if (node == NULL)
    {
        return 0;
    }
    return 1 + countNodes(node->left) + countNodes(node->right);
}

/**
 * @brief Searches for a word in the tree and returns its frequency
 * @param word the word to search for
 * @param node pointer to current node
 * @returns the frequency of the word if found, 0 if not found
 */
uint64_t findWordFrequency(const char *word, struct Node *node)
{
    if (node == NULL || word == NULL)
    {
        return 0;
    }

    int compared = strcmp(word, node->word);

    if (compared == 0)
    {
        return node->frequency;
    }
    else if (compared < 0)
    {
        return findWordFrequency(word, node->left);
    }
    else
    {
        return findWordFrequency(word, node->right);
    }
}

/// Global word counter for file writing (resettable for testing)
uint64_t g_wordCounter = 1;

/**
 * @brief Resets the word counter used by writeContentOfTreeToFile
 * @returns void
 */
void resetWordCounter()
{
    g_wordCounter = 1;
}

/**
 * @brief Writes contents of tree to another file alphabetically
 * @param node pointer to current node
 * @param file pointer to file
 * @returns void
 */
void writeContentOfTreeToFile(struct Node *node, FILE *file)
{
    if (node != NULL)       // checks if the node is valid
    {
        writeContentOfTreeToFile(
            node->left,
            file);  // calls `writeContentOfTreeToFile` for left sub tree
        fprintf(file, "%-5lu \t %-9lu \t %s \n", g_wordCounter++, node->frequency,
                node->word);  // prints the word number, word frequency and word
                              // in tabular format to the file
        writeContentOfTreeToFile(
            node->right,
            file);  // calls `writeContentOfTreeToFile` for right sub tree
    }
}

/**
 * @brief Adds word (node) to the correct position in tree
 * @param word word to be inserted in to the tree
 * @param currentNode node which is being compared
 * @returns a pointer to the root node
 */
struct Node *addWordToTree(char *word, struct Node *currentNode)
{
    if (currentNode == NULL)  // checks if `currentNode` is `NULL`
    {
        struct Node *currentNode =
            allocateMemoryForNode();  // allocates memory for new node
        currentNode->word = getPointerToWord(word);  // stores `word` in memory
        currentNode->frequency = 1;  // initializes the word frequency to 1
        currentNode->left = NULL;    // sets left node to `NULL`
        currentNode->right = NULL;   // sets right node to `NULL`
        return currentNode;          // returns pointer to newly created node
    }

    int64_t compared = strcmp(word, currentNode->word);  ///< holds compare state

    if (compared > 0) {
        currentNode->right = addWordToTree(word,
            currentNode->right);  // adds `word` to right sub tree if `word` is
                                  // alphabetically greater than `currentNode->word`
    }
    else if (compared < 0) {
        currentNode->left = addWordToTree(word,
            currentNode->left);  // adds `word` to left sub tree if `word` is
                                 // alphabetically less than `currentNode->word`
    }
    else {
        currentNode->frequency++; // increments `currentNode` frequency if `word` is the same as `currentNode->word`
    }

    return currentNode; // returns pointer to current node
}

/**
 * @brief Reads words from a string to tree (testable alternative to file-based function)
 * @param text the input string containing words
 * @param root root node of tree
 * @returns a pointer to the root node
 */
struct Node *readWordsFromString(const char *text, struct Node *root)
{
    if (text == NULL)
    {
        return root;
    }

    char *inputString =
        (char *)malloc(46 * sizeof(char));

    if (inputString == NULL)
    {
        endProgramAbruptly("\nA problem occurred while reserving memory for input string\n");
        return root;
    }

    bool isPrevCharAlpha = false;
    uint8_t pos = 0;
    size_t i = 0;

    while (text[i] != '\0')
    {
        char inputChar = text[i++];

        if (pos > 0)
            isPrevCharAlpha = isalpha(inputString[pos - 1]);

        if (isalpha(inputChar))
        {
            inputString[pos++] = tolower(inputChar);
            continue;
        }

        if ((inputChar == '\'' || inputChar == '-') && isPrevCharAlpha)
        {
            inputString[pos++] = inputChar;
            continue;
        }

        if (pos == 0)
            continue;

        if (!isPrevCharAlpha && inputString[pos - 1] != '\'')
            pos--;
        inputString[pos] = '\0';
        pos = 0;
        isPrevCharAlpha = false;
        root = addWordToTree(inputString, root);
    }

    if (pos > 0)
    {
        if (!isPrevCharAlpha && inputString[pos - 1] != '\'')
            pos--;
        inputString[pos] = '\0';
        root = addWordToTree(inputString, root);
    }

    free(inputString);
    return root;
}

/**
 * @brief Reads words from file to tree
 * @param file file to be read from
 * @param root root node of tree
 * @returns a pointer to the root node
 */
struct Node *readWordsInFileToTree(FILE *file, struct Node *root)
{
    // longest english word = 45 chars
    // +1 for '\0' = 46 chars
    char *inputString =
        (char *)malloc(46 * sizeof(char));  ///< pointer to the input string

    if (inputString == NULL)
    {
        endProgramAbruptly("\nA problem occurred while reserving memory for input string\n");
        return root;
    }

    int inputChar;                 ///< temp storage of characters (int for EOF detection)
    bool isPrevCharAlpha = false;  ///< bool to mark the end of a word
    uint8_t pos = 0;  ///< position in inputString to place the inputChar

    while ((inputChar = fgetc(file)) != EOF)
    {
        if (pos > 0)
            isPrevCharAlpha = isalpha(inputString[pos - 1]);

        // checks if character is letter
        if (isalpha(inputChar))
        {
            inputString[pos++] = tolower(inputChar);
            continue;
        }

        // checks if character is ' or - and if it is preceded by a letter eg
        // yours-not, persons' (valid)
        if ((inputChar == '\'' || inputChar == '-') && isPrevCharAlpha)
        {
            inputString[pos++] = inputChar;
            continue;
        }

        // makes sure that there is something valid in inputString
        if (pos == 0)
            continue;

        // if last character is not letter and is not ' then replace by \0
        if (!isPrevCharAlpha && inputString[pos - 1] != '\'')
            pos--;
        inputString[pos] = '\0';
        pos = 0;
        isPrevCharAlpha = false;
        root = addWordToTree(inputString, root);
    }

    // this is to catch the case for the EOF being immediately after the last
    // letter or '
    if (pos > 0)
    {
        if (!isPrevCharAlpha && inputString[pos - 1] != '\'')
            pos--;
        inputString[pos] = '\0';
        root = addWordToTree(inputString, root);
    }

    free(inputString);
    return root;
}
