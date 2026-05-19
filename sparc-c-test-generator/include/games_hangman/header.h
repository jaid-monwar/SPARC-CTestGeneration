/**
 * @file header.h
 * @brief Header file for Hangman Game implementation
 * @details Contains declarations for the hangman game functions and structures
 */

#ifndef GAMES_HANGMAN_H
#define GAMES_HANGMAN_H

#include <stdlib.h>

/**
 * @brief game_instance structure that holds current state of game
 */
struct game_instance {
    char current_word[30]; ///< word to be guessed by player
    char hidden[30];       ///< hidden version of word that is displayed to player
    int size;              ///< size of word
    int incorrect;         ///< number of incorrect guesses
    char guesses[25];      ///< previous guesses
    int guesses_size;      ///< size of guesses array
};

// Core game functions
struct game_instance new_game(void);
struct game_instance new_game_from_word(const char *word);
struct game_instance new_game_from_words(const char *words[], int num_words);
void init_game_instance(struct game_instance *game, const char *word);

// Game logic functions
int new_guess(char new_guess, const char guesses[], int size);
int in_word(char letter, const char word[], int size);
int process_guess(struct game_instance *game, char guess);

// Display functions
void picture(int score);
void won(const char word[], int score);

// Utility functions for testing
int get_remaining_guesses(const struct game_instance *game);
int is_game_won(const struct game_instance *game);
int is_game_lost(const struct game_instance *game);
int get_revealed_count(const struct game_instance *game);
int get_hidden_count(const struct game_instance *game);

#endif /* GAMES_HANGMAN_H */
