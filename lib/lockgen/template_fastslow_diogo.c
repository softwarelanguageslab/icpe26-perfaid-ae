#define _GNU_SOURCE
#include <vsync/spinlock/mcslock.h>
#include <vsync/spinlock/caslock.h>
#include <tilt.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

typedef struct tilt_mutex {
    mcslock_t slow;
    caslock_t fast;
} tilt_mutex_t;

static void tilt_mutex_init(tilt_mutex_t *m)
{
    caslock_init(&m->fast);
    mcslock_init(&m->slow);
}

static void tilt_mutex_destroy(tilt_mutex_t *m)
{
    (void) m;
}

static void tilt_mutex_lock(tilt_mutex_t *m)
{
    mcs_node_t node;
    if (tilt_mutex_trylock(m))
        return;
    mcslock_acquire(&m->slow, &node);
    caslock_acquire(&m->fast);
    mcslock_release(&m->slow, &node);
}

static void tilt_mutex_unlock(tilt_mutex_t *m)
{
    caslock_release(&m->fast);
}

static bool tilt_mutex_trylock(tilt_mutex_t *m)
{
    return caslock_tryacquire(&m->fast);
}
