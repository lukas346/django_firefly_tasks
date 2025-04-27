class AsyncFuncNotSupportedException(Exception):
    """
    Async function not supported, call @atask.
    """


class SyncFuncNotSupportedException(Exception):
    """
    Sync function not supported, call @task.
    """
