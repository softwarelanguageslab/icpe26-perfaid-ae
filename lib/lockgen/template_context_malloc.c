#define _GNU_SOURCE
#include <${SPINLOCK_INCLUDE_PATH}/${LOCK}.h>
#include <tilt.h>
#include <stdlib.h>
#include <stdio.h> // For perror and fprintf

typedef struct tilt_mutex {
    ${LOCK}_t lock;
    ${CONTEXT_TYPE}* context; // Pointer to context
    bool initialized;
} tilt_mutex_t;

static void tilt_mutex_init(tilt_mutex_t *m)
{
    ${LOCK}_init(&m->lock);
    m->context = NULL;
    m->initialized = true;
    fprintf(stderr, "Initialized tilt_mutex: %p\n", (void *)m);
}

static void tilt_mutex_destroy(tilt_mutex_t *m)
{
    if (m->context != NULL) {
        fprintf(stderr, "Warning: Destroying tilt_mutex with non-NULL context: %p\n", (void *)m->context);
        free(m->context);
        m->context = NULL;
    }
    m->initialized = false;
    fprintf(stderr, "Destroyed tilt_mutex: %p\n", (void *)m);
}

static void tilt_mutex_lock(tilt_mutex_t *m)
{
    ${CONTEXT_TYPE} *node = malloc(sizeof(${CONTEXT_TYPE}));
    if (!node) {
        perror("Failed to allocate memory for context in tilt_mutex_lock");
        exit(EXIT_FAILURE);
    }
    ${LOCK}_acquire(&m->lock, node);
    m->context = node;
    fprintf(stderr, "Locked tilt_mutex: %p with context: %p\n", (void *)m, (void *)node);
}

static void tilt_mutex_unlock(tilt_mutex_t *m)
{
    if (!m->context) {
        fprintf(stderr, "Error: Attempting to unlock tilt_mutex with NULL context: %p\n", (void *)m);
        exit(EXIT_FAILURE);
    }
    ${CONTEXT_TYPE} *node = m->context;
    m->context = NULL;
    ${LOCK}_release(&m->lock, node);
    free(node);
    fprintf(stderr, "Unlocked tilt_mutex: %p and freed context: %p\n", (void *)m, (void *)node);
}

static bool tilt_mutex_trylock(tilt_mutex_t *m)
{
    ${CONTEXT_TYPE} *node = malloc(sizeof(${CONTEXT_TYPE}));
    if (!node) {
        perror("Failed to allocate memory for context in tilt_mutex_trylock");
        exit(EXIT_FAILURE);
    }
    const bool result = ${LOCK}_tryacquire(&m->lock, node);
    if (result) {
        m->context = node;
        fprintf(stderr, "Successfully trylocked tilt_mutex: %p with context: %p\n", (void *)m, (void *)node);
    } else {
        free(node);
        fprintf(stderr, "Failed to trylock tilt_mutex: %p, freed temporary context: %p\n", (void *)m, (void *)node);
    }
    return result;
}
