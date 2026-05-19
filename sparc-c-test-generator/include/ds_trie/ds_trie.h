/*------------------Trie Data Structure----------------------------------*/
/*-------------Header file for trie data structure-----------------------*/

#ifndef DS_TRIE_H
#define DS_TRIE_H

#include <stdbool.h>

#define ALPHABET_SIZE 26

/*--Node in the Trie--*/
struct trie {
    struct trie *children[ALPHABET_SIZE];
    bool end_of_word;
};

/*--Create new trie node--*/
int trie_new(struct trie ** trie);

/*--Insert new word to Trie--*/
int trie_insert(struct trie * trie, char *word, unsigned word_len);

/*--Search a word in the Trie--*/
int trie_search(struct trie * trie, char *word, unsigned word_len, struct trie ** result);

/*--Print all words with given prefix--*/
void trie_print(struct trie * trie, char prefix[], unsigned prefix_len);

/*--Free trie recursively--*/
void trie_free(struct trie * trie);

/*--Count total nodes in trie--*/
int trie_count_nodes(struct trie * trie);

/*--Count total words in trie--*/
int trie_count_words(struct trie * trie);

/*--Check if word exists in trie (returns 1 if found, 0 otherwise)--*/
int trie_contains(struct trie * trie, char *word, unsigned word_len);

/*--Insert word from null-terminated string--*/
int trie_insert_string(struct trie * trie, const char *word);

/*--Check if string exists in trie--*/
int trie_contains_string(struct trie * trie, const char *word);

/*--Check if trie is empty (no words)--*/
int trie_is_empty(struct trie * trie);

/*--Get number of children for a node--*/
int trie_get_child_count(struct trie * trie);

/*--Check if node is a leaf (no children)--*/
int trie_is_leaf(struct trie * trie);

/*--Get trie node for prefix (for testing traversal)--*/
int trie_get_prefix_node(struct trie * trie, const char *prefix, struct trie ** result);

/*--Insert words from string array (for bulk testing)--*/
int trie_insert_words(struct trie * trie, const char **words, int word_count);

/*--Check if all words from array exist in trie--*/
int trie_contains_all(struct trie * trie, const char **words, int word_count);

/*--Collect all words starting with prefix into array--*/
int trie_collect_words(struct trie * trie, const char *prefix, char **buffer, int max_words);

/*--Free collected words buffer--*/
void trie_free_collected_words(char **buffer, int count);

#endif /* DS_TRIE_H */
