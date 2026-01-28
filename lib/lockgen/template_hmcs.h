#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h> // For abort

#include <${SPINLOCK_INCLUDE_PATH}/${LOCK}.h>

static inline vsize_t cid_of_cur_thread(void) {
    int cpu = sched_getcpu();
    if (cpu < 0) {
        perror("sched_getcpu failed");
        abort();
    }
    return (vsize_t)cpu;
}

#define MAX_THREADS 512u

${hierarchy_defines}

#define HMCS_CPU_P_CORE ((HMCS_NB_CPUS) / (HMCS_NB_CORES))

${h_thresholds_defines}

#define NUM_LEVELS ${nb_levels}
${level_sizes}
#define CPUS_PER_LEAF_NODE ${cpus_per_leaf_node}

${thresholds}

#define NUM_LOCKS ( \
${num_locks}
)

#define LEVEL_SPEC { \
${level_spec}
}

typedef struct numa_hmcs_node_s {
    hmcs_node_t qnode;
    vsize_t current_core;
} numa_hmcs_node_t;

typedef struct numa_hmcslock_s {
    hmcslock_t hmcs_locks[NUM_LOCKS]; // array of hmcs locks
    hmcslock_t *leaf_locks[MAX_THREADS];
} numa_hmcslock_t;

static void
numa_hmcslock_init(numa_hmcslock_t* lock)
{
    hmcslock_level_spec_t level_specs[NUM_LEVELS] = LEVEL_SPEC;

    hmcslock_init(lock->hmcs_locks, NUM_LOCKS, level_specs, NUM_LEVELS);
    for (vuint32_t i = 0; i < MAX_THREADS; i++) {
        lock->leaf_locks[i] = hmcslock_which_lock(
            lock->hmcs_locks,
            NUM_LOCKS,
            level_specs,
            NUM_LEVELS,
            CPUS_PER_LEAF_NODE,
            i
        );
    }
}

static void
numa_hmcslock_acquire(numa_hmcslock_t* lock, numa_hmcs_node_t *node)
{
    const vsize_t cpuid = cid_of_cur_thread();
    node->current_core = cpuid;
    const vsize_t vcpuid = (cpuid % HMCS_NB_CORES) * HMCS_CPU_P_CORE + (cpuid / HMCS_NB_CORES);

    hmcslock_acquire(
        lock->leaf_locks[vcpuid],
        &(node->qnode),
        NUM_LEVELS
    );
}

static void
numa_hmcslock_release(numa_hmcslock_t* lock, numa_hmcs_node_t *node)
{
//    const vsize_t cpuid = cid_of_cur_thread();
    const vsize_t cpuid = node->current_core;
    const vsize_t vcpuid = (cpuid % HMCS_NB_CORES) * HMCS_CPU_P_CORE + (cpuid / HMCS_NB_CORES);

    hmcslock_release(
        lock->leaf_locks[vcpuid],
        &(node->qnode),
        NUM_LEVELS
    );
}
