from contextlib import ExitStack, contextmanager


@contextmanager
def nested(*contexts):
    with ExitStack() as stack:
        results = []
        for ctx in contexts:
            results.append(stack.enter_context(ctx))
        yield results
