def task_as_dict(task) -> dict:
    """
    Simple dict repr of a task.
    """
    return {
        "id": task.id,
        "func_name": task.func_name,
        "status": task.status,
        "not_before": task.not_before,
        "created": task.created,
        "retry_attempts": task.retry_attempts,
        "retry_delay": f"{task.retry_delay}s",
        "max_retries": task.max_retries,
    }
