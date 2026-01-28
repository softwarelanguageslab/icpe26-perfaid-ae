#define _GNU_SOURCE
#include <${SPINLOCK_INCLUDE_PATH}/${LOCK}.h>
#include <tilt.h>
#include <stdlib.h>
#include <stdio.h>

typedef struct tilt_mutex {
    ${LOCK}_t lock;
} tilt_mutex_t;

static void tilt_mutex_init(tilt_mutex_t *m)
{
    ${LOCK}_init(&m->lock);
}

static void tilt_mutex_destroy(tilt_mutex_t *m)
{
${DESTROY_IMPLEMENTATION}
}

static void tilt_mutex_lock(tilt_mutex_t *m)
{
    ${LOCK}_acquire(&m->lock);
}

static void tilt_mutex_unlock(tilt_mutex_t *m)
{
    ${LOCK}_release(&m->lock);
}

static bool tilt_mutex_trylock(tilt_mutex_t *m)
{
${TRYACQUIRE_IMPLEMENTATION}
}
