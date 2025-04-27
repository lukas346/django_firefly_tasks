from .models import TaskModel


def task_as_dict(task: TaskModel) -> dict:
    return {
        "id": task.id,
        "func_name": task.func_name,
        "status": task.status,
        "not_before": task.not_before,
        "created": task.created,
        "restart_attempts": task.restart_attempts,
        "restart_delay": f"{task.restart_delay}s",
        "max_restarts": task.max_restarts
    }
