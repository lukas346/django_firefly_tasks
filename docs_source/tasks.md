
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
```

---

###  `django_firefly_tasks.decorators.atask`  
Supports **asynchronous** functions.

```python
@atask()
async def foo():
    pass
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
