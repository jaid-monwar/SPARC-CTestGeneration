#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


// Struct definitions
typedef struct trie {
    struct trie * children;
    _Bool end_of_word;
} trie;

// Macros
#define _POSIX_C_SOURCE
#define ALPHABET_SIZE
// Function declarations
int trie_new(struct trie * * trie);
int trie_insert(struct trie * trie, char * word, unsigned int word_len);
int trie_search(struct trie * trie, char * word, unsigned int word_len, struct trie * * result);
void trie_print(struct trie * trie, char prefix[], unsigned int prefix_len);
void trie_free(struct trie * trie);
int trie_count_nodes(struct trie * trie);
int trie_count_words(struct trie * trie);
int trie_contains(struct trie * trie, char * word, unsigned int word_len);
int trie_insert_string(struct trie * trie, const char * word);
int trie_contains_string(struct trie * trie, const char * word);
int trie_is_empty(struct trie * trie);
int trie_get_child_count(struct trie * trie);
int trie_is_leaf(struct trie * trie);
int trie_get_prefix_node(struct trie * trie, const char * prefix, struct trie * * result);
int trie_insert_words(struct trie * trie, const char * * words, int word_count);
int trie_contains_all(struct trie * trie, const char * * words, int word_count);
void trie_collect_words_helper(struct trie * trie, char prefix[], unsigned int prefix_len, char * * buffer, int * buffer_index, int max_words);
int trie_collect_words(struct trie * trie, const char * prefix, char * * buffer, int max_words);
void trie_free_collected_words(char * * buffer, int count);

#endif
