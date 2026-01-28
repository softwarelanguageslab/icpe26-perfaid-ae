#define _GNU_SOURCE
// To avoid overloading the pthread_mutex struct (override libvsync value):
#define VSYNC_CACHELINE_SIZE 8

#include <${SPINLOCK_INCLUDE_PATH}/${LOCK}.h>
#include <tilt.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

#define MAX_CONTEXTS 16 // Maximum number of nested locks per thread

typedef struct tilt_mutex {
    ${LOCK}_t lock;
    vatomic32_t init_stage; // 0 = uninitialized, 1 = init in progress, 2 = initialized
} tilt_mutex_t;

// Thread-local storage for contexts and counter
static __thread ${CONTEXT_TYPE} tls_contexts[MAX_CONTEXTS];
static __thread int tls_context_counter = 0;

static_assert(sizeof(tilt_mutex_t) <= 40, "mutex too large");

static void tilt_mutex_lazy_init(tilt_mutex_t *m)
{
    while (vatomic32_read(&m->init_stage) != 2) {
        if (!vatomic32_cmpxchg(&m->init_stage, 0, 1)) {
            // We are responsible for initialization
            ${LOCK}_init(&m->lock);
            vatomic32_write(&m->init_stage, 2); // Mark as initialized
        }
        // If another thread is initializing, wait for it to finish
        while (vatomic32_read(&m->init_stage) == 1) {
            // Optional: add a yield or pause to avoid busy-waiting
        }
    }
}

static void tilt_mutex_init(tilt_mutex_t *m)
{
    tilt_mutex_lazy_init(m); // Explicitly initialize
}

static void tilt_mutex_destroy(tilt_mutex_t *m)
{
    tilt_mutex_lazy_init(m); // Ensure lock is initialized
    if (vatomic32_cmpxchg(&m->init_stage, 2, 1)) { // Transition to 'in progress' only if initialized
        ${DESTROY_IMPLEMENTATION}
        vatomic32_write(&m->init_stage, 0); // Mark as uninitialized
    }
    // If another thread is already destroying, just return
}

static void tilt_mutex_lock(tilt_mutex_t *m)
{
    tilt_mutex_lazy_init(m); // Ensure lock is initialized
    assert(tls_context_counter < MAX_CONTEXTS && "Exceeded maximum nested locks");
    ${CONTEXT_TYPE} *node = &tls_contexts[tls_context_counter++];${NODE_INIT}
    ${LOCK}_acquire(&m->lock, node);
}

static void tilt_mutex_unlock(tilt_mutex_t *m)
{
    assert(tls_context_counter > 0 && "Unlock called without a matching lock");
    ${CONTEXT_TYPE} *node = &tls_contexts[--tls_context_counter];
    ${LOCK}_release(&m->lock, node);
}

static bool tilt_mutex_trylock(tilt_mutex_t *m)
{
    tilt_mutex_lazy_init(m); // Ensure lock is initialized
    ${TRYACQUIRE_IMPLEMENTATION}
}
