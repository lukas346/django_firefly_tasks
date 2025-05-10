
# Task Guide

Task metadata is an entity stored in your **database of choice** and consumed by a worker. Parameters and returned data are pickled and stored as a Base64 string for compatibility.  ⚠️ **Keep the data as small as possible** — prefer using *primitive types* instead of complex objects.

All operations in task/function are wrapped in a `transaction.atomic` block.

If the queue is always full, deferred tasks may never get executed again.

### `django_firefly_tasks.decorators.task`  
Supports **synchronous** functions.

```python
@task()
def foo():
    pass

# foo.schedule()
```

---

###  `django_firefly_tasks.decorators.atask`  
Supports **asynchronous** functions.

```python
@atask()
async def foo():
    pass

# await foo.schedule()
```

---

## ⚙️ Parameters

- **queue** (*str*): the queue in which the task will be placed (default = `"default"`)
- **max_retries** (*int*): maximum number of retries on failure (default = `0`)
- **retry_delay** (*int*): delay in seconds between retries (default = `120`)

---

## How to Use

### 1️⃣ Define the function

```python
def add(i: int, j: int) -> int:
    return i + j
```

### 2️⃣ Decorate it

```python
@task(queue="default", max_retries=0, retry_delay=0)
def add(i: int, j: int) -> int:
    return i + j
```

### 3️⃣ Schedule the task (in views, models, serializers, forms, etc.)

```python
task = add.schedule(1, 3)
```

A `TaskModel` instance is returned. It stores metadata about the scheduled task.

### 4️⃣ Retrieve returned data after processing

```python
task = TaskModel.objects.get(pk=task.id)
returned_data = task.returned # 4
```

---

##  Consumer

A consumer is required to process tasks. Use the Django management command:

```bash
./manage.py consume_tasks
```

To define a specific queue:

```bash
./manage.py consume_tasks --queue default
```

---

## Task Restarting

You can configure task restarting with the following parameters:

- `max_retries`: how many times the task should retry on failure  
- `retry_delay`: delay (in seconds) between retries

**Example:**

```python
@task(max_retries=20, retry_delay=100)
```

This will retry the task up to 20 times, waiting 100 seconds between each attempt.


---

## Task with Time

You can schedule a task to run at a specific datetime using `eta` parameter in `schedule` method. 

**Example:**

```python
add.schedule(1, 3, eta=datetime(2025, 3, 30, 18, 30, tzinfo=ZoneInfo("UTC")))
```

This will attempt to run the task on March 30, 2025 at 18:30 UTC. However, be aware of the [task consumption order](https://lukas346.github.io/django_firefly_tasks/commands.html#consume-tasks), as it may affect the exact execution time.

---

## Running a Task Inside Another Task
You can invoke a task from within another task.

```python
@task()
def schedule_task():
    add.schedule(1, 3)
```

When doing so, make sure to call synchronous tasks from within other synchronous tasks, and asynchronous tasks from within asynchronous tasks:

```python
@atask()
async def async_schedule_task():
    await async_add.schedule(1, 3)
```

If necessary, you can use `sync_to_async` or `async_to_sync` to bridge between sync and async contexts:

```python
from asgiref.sync import async_to_sync

@task()
def schedule_task():
    async_to_sync(async_add.schedule)(1, 3)
```

---

## Task Entity Structure

- **id** (*int*): task id
- **func_name** (*str*): function name with the path in dot notation  
- **queue** (*str*): target queue  
- **status** (*str*): status of the task (`created`, `completed`, `failed`)  
- **created** (*datetime*): time of creation  
- **completed** (*datetime*): time of successful completion  
- **failed** (*datetime*): time of failure  
- **not_before** (*datetime*): task will not run before this datetime  
- **params** (*any*): parameters passed to the function  
- **returned** (*any*): value returned by the function  
