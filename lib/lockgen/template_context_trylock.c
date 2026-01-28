    assert(tls_context_counter < MAX_CONTEXTS && "Exceeded maximum nested locks");
    ${CONTEXT_TYPE} *node = &tls_contexts[tls_context_counter];
    const bool result = ${LOCK}_tryacquire(&m->lock, node);
    if (result) {
        tls_context_counter++;
    }
    return result;
