/*
 * Stdout Capture Helper Functions
 *
 * These functions provide a portable way to capture stdout output in C tests.
 * Use these helpers when testing functions that print to stdout (printf, puts, etc.).
 *
 * IMPORTANT: Do NOT try to redirect stdout by assigning to it (stdout = newfile).
 * That approach is invalid in C. Use these helpers instead.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Structure to hold stdout capture state.
 * Created by capture_stdout_start(), freed by capture_stdout_stop().
 */
typedef struct {
    int saved_stdout_fd;    /* Original stdout file descriptor */
    int pipe_read_fd;       /* Read end of pipe */
    int pipe_write_fd;      /* Write end of pipe */
    char *buffer;           /* Captured output buffer */
    size_t buffer_size;     /* Size of allocated buffer */
} stdout_capture_t;

/*
 * Start capturing stdout output.
 * Returns a capture context that must be passed to capture_stdout_stop().
 * Returns NULL on failure.
 *
 * Usage:
 *   stdout_capture_t *cap = capture_stdout_start();
 *   printf("Hello");  // This output will be captured
 *   char *output = capture_stdout_stop(cap);
 *   // output now contains "Hello"
 *   free(output);
 */
stdout_capture_t *capture_stdout_start(void) {
    stdout_capture_t *cap = malloc(sizeof(stdout_capture_t));
    if (!cap) return NULL;

    cap->buffer = NULL;
    cap->buffer_size = 0;

    /* Create a pipe */
    int pipefd[2];
    if (pipe(pipefd) == -1) {
        free(cap);
        return NULL;
    }
    cap->pipe_read_fd = pipefd[0];
    cap->pipe_write_fd = pipefd[1];

    /* Save original stdout */
    cap->saved_stdout_fd = dup(STDOUT_FILENO);
    if (cap->saved_stdout_fd == -1) {
        close(cap->pipe_read_fd);
        close(cap->pipe_write_fd);
        free(cap);
        return NULL;
    }

    /* Redirect stdout to the pipe write end */
    if (dup2(cap->pipe_write_fd, STDOUT_FILENO) == -1) {
        close(cap->saved_stdout_fd);
        close(cap->pipe_read_fd);
        close(cap->pipe_write_fd);
        free(cap);
        return NULL;
    }

    return cap;
}

/*
 * Stop capturing stdout and return the captured output.
 * Restores original stdout behavior.
 * Returns a newly allocated string containing the captured output.
 * The caller must free() the returned string.
 * Returns NULL on failure.
 */
char *capture_stdout_stop(stdout_capture_t *cap) {
    if (!cap) return NULL;

    /* Flush stdout to ensure all output is written to pipe */
    fflush(stdout);

    /* Close write end of pipe to signal EOF */
    close(cap->pipe_write_fd);

    /* Restore original stdout */
    dup2(cap->saved_stdout_fd, STDOUT_FILENO);
    close(cap->saved_stdout_fd);

    /* Read captured output from pipe */
    size_t total_read = 0;
    size_t buffer_capacity = 1024;
    char *buffer = malloc(buffer_capacity);
    if (!buffer) {
        close(cap->pipe_read_fd);
        free(cap);
        return NULL;
    }

    ssize_t bytes_read;
    while ((bytes_read = read(cap->pipe_read_fd, buffer + total_read,
                               buffer_capacity - total_read - 1)) > 0) {
        total_read += bytes_read;
        if (total_read >= buffer_capacity - 1) {
            buffer_capacity *= 2;
            char *new_buffer = realloc(buffer, buffer_capacity);
            if (!new_buffer) {
                free(buffer);
                close(cap->pipe_read_fd);
                free(cap);
                return NULL;
            }
            buffer = new_buffer;
        }
    }

    buffer[total_read] = '\0';

    close(cap->pipe_read_fd);
    free(cap);

    return buffer;
}

/*
 * Assert that stdout output matches the expected string.
 * This is a convenience function that combines capture and assertion.
 *
 * Usage:
 *   stdout_capture_t *cap = capture_stdout_start();
 *   printf("Hello, World!");
 *   assert_stdout_equals(cap, "Hello, World!");
 */
void assert_stdout_equals(stdout_capture_t *cap, const char *expected) {
    char *actual = capture_stdout_stop(cap);
    if (actual == NULL) {
        fprintf(stderr, "Stdout capture failed\n");
        exit(1);
    }
    if (strcmp(actual, expected) != 0) {
        fprintf(stderr, "Stdout assertion failed:\n");
        fprintf(stderr, "  Expected: \"%s\"\n", expected);
        fprintf(stderr, "  Actual:   \"%s\"\n", actual);
        free(actual);
        exit(1);
    }
    free(actual);
}

/*
 * Assert that stdout output contains the expected substring.
 *
 * Usage:
 *   stdout_capture_t *cap = capture_stdout_start();
 *   printf("Hello, World!");
 *   assert_stdout_contains(cap, "World");
 */
void assert_stdout_contains(stdout_capture_t *cap, const char *expected_substring) {
    char *actual = capture_stdout_stop(cap);
    if (actual == NULL) {
        fprintf(stderr, "Stdout capture failed\n");
        exit(1);
    }
    if (strstr(actual, expected_substring) == NULL) {
        fprintf(stderr, "Stdout assertion failed (substring not found):\n");
        fprintf(stderr, "  Expected substring: \"%s\"\n", expected_substring);
        fprintf(stderr, "  Actual output:      \"%s\"\n", actual);
        free(actual);
        exit(1);
    }
    free(actual);
}

/*
 * Assert that stdout output is not empty.
 * Useful for testing functions that should produce some output.
 *
 * Usage:
 *   stdout_capture_t *cap = capture_stdout_start();
 *   print_something();
 *   assert_stdout_not_empty(cap);
 */
void assert_stdout_not_empty(stdout_capture_t *cap) {
    char *actual = capture_stdout_stop(cap);
    if (actual == NULL) {
        fprintf(stderr, "Stdout capture failed\n");
        exit(1);
    }
    if (strlen(actual) == 0) {
        fprintf(stderr, "Stdout assertion failed: output was empty\n");
        free(actual);
        exit(1);
    }
    free(actual);
}
