# Django Commands

Custom django commands provided by the Django Firefly Tasks.

## Consume tasks

Consumes scheduled tasks. Default queue is called "default". **Consumer doesn't have auto-reload, so when tasks changed it requires manual restart.** 

Consuming order: `created, not retried`, `closest retries`, `eta`, `the most distant in time retries`

```bash
python manage.py consume_tasks [--queue QUEUE]
```

## Delete Completed Tasks

Deletes completed tasks.

```bash
python manage.py delete_completed_tasks
```

## Delete Failed Tasks

Deletes failed tasks.

```bash
python manage.py delete_failed_tasks
```

## Mark Failed Tasks Consumable

Marks failed tasks as ready to consume.

```bash
python manage.py mark_failed_tasks_consumable
```
