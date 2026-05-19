#ifndef HEADER_H
#define HEADER_H

// Includes from source file
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>


// Struct definitions
typedef struct ASTNode {
    char content;
    struct ASTNode * left;
    struct ASTNode * right;
} ASTNode;

typedef struct transRule {
    struct NFAState * target;
    char cond;
} transRule;

typedef struct NFAState {
    int ruleCount;
    struct transRule * * rules;
} NFAState;

typedef struct NFA {
    int stateCount;
    struct NFAState * * statePool;
    int ruleCount;
    struct transRule * * rulePool;
    int CSCount;
    struct NFAState * * currentStates;
    int subCount;
    struct NFA * * subs;
    int wrapperFlag;
} NFA;

// Function declarations
int isLiteral(const char ch);
char * preProcessing(const char * input);
size_t indexOf(const char * str, char key);
char * subString(const char * str, size_t begin, size_t end);
struct ASTNode * buildAST(const char * input);
void redirect(struct NFA * nfa, struct NFAState * src, struct NFAState * dest);
struct NFA * compileFromAST(struct ASTNode * root);
void addState(struct NFA * nfa, struct NFAState * state);
void addRule(struct NFA * nfa, struct transRule * rule, int loc);
void postProcessing(struct NFA * nfa);
int contains(struct NFAState * * states, int len, struct NFAState * state);
void findEmpty(struct NFAState * target, struct NFAState * * states, int * sc);
void transit(struct NFA * nfa, char input);
int isAccepting(const struct NFA * nfa);
void testHelper(const char * regex, const char * string, const int expected);
void test(void);
struct ASTNode * createNode(const char content);
void destroyNode(struct ASTNode * node);
struct transRule * createRule(struct NFAState * state, char c);
void destroyRule(struct transRule * rule);
struct NFAState * createState(void);
void destroyState(struct NFAState * state);
struct NFA * createNFA(void);
void destroyNFA(struct NFA * nfa);

#endif
