/**
 * @file
 * @brief C implementation of [Hangman Game](https://en.wikipedia.org/wiki/Hangman_(game))
 * @details
 * Simple, readable version of hangman.
 * Changed graphic to duck instead of traditional stick figure (same number of guesses).
 * @author [AtlantaEmrys2002](https://github.com/AtlantaEmrys2002)
 * @modified Made testable for unit testing pipeline
*/

#include <ctype.h> /// for tolower()
#include <stdio.h> /// for I/O operations
#include <stdlib.h> /// for exit(), rand() and memory functions
#include <string.h> /// for string operations strlen, strchr, strcpy
#include <time.h> /// for srand()

#include "header.h"

/**
 * @brief checks if letter has been guessed before
 * @param new_guess letter that has been guessed by player
 * @param guesses array of player's previous guesses
 * @param size size of guesses[] array
 * @returns 1 if letter has been guessed before
 * @returns -1 if letter has not been guessed before
 */
int new_guess(char new_guess, const char guesses[], int size) {
    if (guesses == NULL || size < 0) {
        return -1;
    }

    for (int j = 0; j < size; j++) {
        if (guesses[j] == new_guess) {
            printf("\nYou have already guessed that letter.");
            return 1;
        }
    }

    return -1;
}

/**
 * @brief checks if letter is in current word
 * @param letter letter guessed by player
 * @param word current word
 * @param size length of word
 * @returns 1 if letter is in word
 * @returns -1 if letter is not in word
 */
int in_word(char letter, const char word[], int size) {
    if (word == NULL || size <= 0) {
        return -1;
    }

    for (int i = 0; i < size; i++) {
        if ((word[i]) == letter) {
            return 1;
        }
    }

    return -1;
}

/**
 * @brief creates a new game - generates a random word and stores in global variable current_word
 * @returns current_game - a new game instance containing randomly selected word, its length and hidden version of word
 */
struct game_instance new_game() {

    char word[30]; // used throughout function

    FILE *fptr;
    fptr = fopen("games/words.txt", "r");

    if (fptr == NULL){
        fprintf(stderr, "File not found.\n");
        exit(EXIT_FAILURE);
    }

    // counts number of words in file - assumes each word on new line
    int line_number = 0;
    while (fgets(word, 30, fptr) != NULL) {
        line_number++;
    }

    rewind(fptr);

    // generates random number
    int random_num;
    srand(time(NULL));
    random_num = rand() % line_number;

    // selects randomly generated word
    int s = 0;
    while (s <= random_num){
        fgets(word, 30, fptr);
        s++;
    }

    // formats string correctly
    if (strchr(word, '\n') != NULL){
        word[strlen(word) - 1] = '\0';
    }

    fclose(fptr);

    // creates new game instance
    struct game_instance current_game;
    strcpy(current_game.current_word, word);
    current_game.size = (int)strlen(word);
    for (int i = 0; i < current_game.size; i++) {
        current_game.hidden[i] = '_';
    }
    current_game.hidden[current_game.size] = '\0';
    current_game.incorrect = 0;
    current_game.guesses_size = 0;
    memset(current_game.guesses, 0, sizeof(current_game.guesses));

    return current_game;
}

/**
 * @brief checks if player has won or lost
 * @param word the word player has attempted to guess
 * @param score how many incorrect guesses player has made
 * @returns void
 */
void won(const char word[], int score) {
    if (score > 12) {
        printf("\nYou lost! The word was: %s.\n", word);
    }
    else {
        printf("\nYou won! You had %d guesses left.\n", (12 - score));
    }
}

/*
 * @brief gradually draws duck as player gets letters incorrect
 * @param score how many incorrect guesses player has made
 * @returns void
 */
void picture(int score) {

    switch(score) {

        case 12:
            printf("\n      _\n"
                   "  __( ' )> \n"
                   " \\_ < _ ) ");
            break;

        case 11:
            printf("\n      _\n"
                   "  __( ' )\n"
                   " \\_ < _ ) ");
            break;

        case 10:
            printf("\n      _\n"
                   "  __(   )\n"
                   " \\_ < _ ) ");
            break;

        case 9:
            printf("\n        \n"
                   "  __(   )\n"
                   " \\_ < _ ) ");
            break;

        case 8:
            printf("\n        \n"
                   "  __(    \n"
                   " \\_ < _ ) ");
            break;

        case 7:
            printf("\n        \n"
                   "  __     \n"
                   " \\_ < _ ) ");
            break;

        case 6:
            printf("\n        \n"
                   "  _      \n"
                   " \\_ < _ ) ");
            break;

        case 5:
            printf("\n        \n"
                   "  _      \n"
                   "   _ < _ ) ");
            break;

        case 4:
            printf("\n        \n"
                   "         \n"
                   "   _ < _ ) ");
            break;

        case 3:
            printf("\n        \n"
                   "         \n"
                   "     < _ ) ");
            break;

        case 2:
            printf("\n        \n"
                   "         \n"
                   "       _ ) ");
            break;

        case 1:
            printf("\n        \n"
                   "         \n"
                   "         ) ");
            break;

        case 0:
            break;

        default:
            printf("\n      _\n"
                   "  __( ' )> QUACK!\n"
                   " \\_ < _ ) ");
            break;
    }
}

/**
 * @brief initializes a game instance with a specific word
 * @param game pointer to game instance to initialize
 * @param word the word to use for the game
 * @returns void
 */
void init_game_instance(struct game_instance *game, const char *word) {
    if (game == NULL || word == NULL) {
        return;
    }

    size_t len = strlen(word);
    if (len >= 30) {
        len = 29; // truncate to fit buffer
    }

    strncpy(game->current_word, word, len);
    game->current_word[len] = '\0';
    game->size = (int)len;

    for (int i = 0; i < game->size; i++) {
        game->hidden[i] = '_';
    }
    game->hidden[game->size] = '\0';

    game->incorrect = 0;
    game->guesses_size = 0;
    memset(game->guesses, 0, sizeof(game->guesses));
}

/**
 * @brief creates a new game with a specific word (string-based alternative to new_game)
 * @param word the word to guess
 * @returns game_instance initialized with the given word
 */
struct game_instance new_game_from_word(const char *word) {
    struct game_instance game;

    if (word == NULL || strlen(word) == 0) {
        // Return empty game instance
        memset(&game, 0, sizeof(game));
        return game;
    }

    init_game_instance(&game, word);
    return game;
}

/**
 * @brief creates a new game selecting randomly from a word list (string-based alternative)
 * @param words array of words to choose from
 * @param num_words number of words in the array
 * @returns game_instance initialized with a randomly selected word
 */
struct game_instance new_game_from_words(const char *words[], int num_words) {
    struct game_instance game;

    if (words == NULL || num_words <= 0) {
        memset(&game, 0, sizeof(game));
        return game;
    }

    // Select random word
    int random_idx = rand() % num_words;
    const char *selected_word = words[random_idx];

    if (selected_word == NULL) {
        memset(&game, 0, sizeof(game));
        return game;
    }

    init_game_instance(&game, selected_word);
    return game;
}

/**
 * @brief processes a single guess and updates game state
 * @param game pointer to game instance
 * @param guess the letter guessed by player
 * @returns 1 if guess was correct, 0 if incorrect, -1 if already guessed or invalid
 */
int process_guess(struct game_instance *game, char guess) {
    if (game == NULL) {
        return -1;
    }

    guess = tolower(guess);

    // Check if already guessed
    if (new_guess(guess, game->guesses, game->guesses_size) != -1) {
        return -1; // Already guessed
    }

    // Add to guesses array
    if (game->guesses_size < 25) {
        game->guesses[game->guesses_size] = guess;
        game->guesses_size++;
    }

    // Check if letter is in word
    if (in_word(guess, game->current_word, game->size) == 1) {
        // Reveal the letter in hidden
        for (int i = 0; i < game->size; i++) {
            if (tolower(game->current_word[i]) == guess) {
                game->hidden[i] = game->current_word[i];
            }
        }
        return 1; // Correct guess
    } else {
        game->incorrect++;
        return 0; // Incorrect guess
    }
}

/**
 * @brief gets the number of remaining guesses
 * @param game pointer to game instance
 * @returns number of remaining guesses, or -1 if game is NULL
 */
int get_remaining_guesses(const struct game_instance *game) {
    if (game == NULL) {
        return -1;
    }
    return 12 - game->incorrect;
}

/**
 * @brief checks if the game has been won
 * @param game pointer to game instance
 * @returns 1 if won (no underscores left), 0 otherwise, -1 if game is NULL
 */
int is_game_won(const struct game_instance *game) {
    if (game == NULL) {
        return -1;
    }

    // Game is won if there are no underscores left in hidden
    for (int i = 0; i < game->size; i++) {
        if (game->hidden[i] == '_') {
            return 0;
        }
    }
    return 1;
}

/**
 * @brief checks if the game has been lost
 * @param game pointer to game instance
 * @returns 1 if lost (more than 12 incorrect), 0 otherwise, -1 if game is NULL
 */
int is_game_lost(const struct game_instance *game) {
    if (game == NULL) {
        return -1;
    }
    return (game->incorrect > 12) ? 1 : 0;
}

/**
 * @brief counts the number of revealed (non-underscore) letters
 * @param game pointer to game instance
 * @returns count of revealed letters, or -1 if game is NULL
 */
int get_revealed_count(const struct game_instance *game) {
    if (game == NULL) {
        return -1;
    }

    int count = 0;
    for (int i = 0; i < game->size; i++) {
        if (game->hidden[i] != '_') {
            count++;
        }
    }
    return count;
}

/**
 * @brief counts the number of hidden (underscore) letters
 * @param game pointer to game instance
 * @returns count of hidden letters, or -1 if game is NULL
 */
int get_hidden_count(const struct game_instance *game) {
    if (game == NULL) {
        return -1;
    }

    int count = 0;
    for (int i = 0; i < game->size; i++) {
        if (game->hidden[i] == '_') {
            count++;
        }
    }
    return count;
}
