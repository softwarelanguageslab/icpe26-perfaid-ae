#define _GNU_SOURCE
#include <${SPINLOCK_INCLUDE_PATH}/${LOCK}.h>
#include <tilt.h>
#include <pthread.h>
#include <stdlib.h>
#include <stdio.h> // Include for perror and fprintf

typedef struct tilt_mutex {
    ${LOCK}_t lock;
    pthread_key_t thread_key; // Key for thread-local storage
    bool initialized;
} tilt_mutex_t;

// Destructor for thread-local storage
static void free_thread_context(void *ctx)
{
    (void) ctx;//TODO remove
//    free(ctx);
}

static void tilt_mutex_init(tilt_mutex_t *m)
{
    ${LOCK}_init(&m->lock);
    const int rc = pthread_key_create(&m->thread_key, free_thread_context); // Register destructor
    if (rc) {
        perror("tilt_mutex_init: Failed to create key for context");
    }
    m->initialized = true;
}

static void tilt_mutex_destroy(tilt_mutex_t *m)
{
    const int rc = pthread_key_delete(m->thread_key);
    if (rc) {
        perror("tilt_mutex_destroy: Failed to delete key for context");
    }
    m->initialized = false;
}

static ${CONTEXT_TYPE} *get_thread_context(tilt_mutex_t *m)
{
    ${CONTEXT_TYPE} *node = pthread_getspecific(m->thread_key);
    if (!node) {
        node = malloc(sizeof(${CONTEXT_TYPE})); // Allocate context for this thread
        if (!node) { // Check for allocation failure
            perror("Failed to allocate memory for mcs_node_t");
            exit(EXIT_FAILURE); // Exit or handle gracefully
        }

        const int rc = pthread_setspecific(m->thread_key, node);
        if (rc) {
            fprintf(stderr, "Error occurred: %d\n", rc);
            fprintf(stderr, "EINVAL = %d\n", EINVAL);
            fprintf(stderr, "ENOMEM = %d\n", ENOMEM);
            perror("get_thread_context: Failed to call setspecific %d");
        }
    }
    return node;
}

static void tilt_mutex_lock(tilt_mutex_t *m)
{
    ${CONTEXT_TYPE} *node = get_thread_context(m);
    ${LOCK}_acquire(&m->lock, node);
}

static void tilt_mutex_unlock(tilt_mutex_t *m)
{
    ${CONTEXT_TYPE} *node = get_thread_context(m);
    ${LOCK}_release(&m->lock, node);

    free(node);
    const int rc = pthread_setspecific(m->thread_key, 0);
    if (rc) {
        perror("tilt_mutex_unlock: Failed to call setspecific to 0");
    }
}

static bool tilt_mutex_trylock(tilt_mutex_t *m)
{
    ${CONTEXT_TYPE} *node = get_thread_context(m);
    return ${LOCK}_tryacquire(&m->lock, node);
}
