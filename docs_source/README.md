<p align="center">
  <img src="https://i.imgur.com/kshLe4w.png">
</p>

[![Package Testing](https://github.com/lukas346/django_firefly_tasks/actions/workflows/testing.yml/badge.svg)](https://github.com/lukas346/django_firefly_tasks/actions/workflows/testing.yml)
[![PyPI version](https://badge.fury.io/py/django-firefly-tasks.svg)](https://badge.fury.io/py/django-firefly-tasks)
[![PyPI Downloads](https://static.pepy.tech/badge/django-firefly-tasks)](https://pepy.tech/projects/django-firefly-tasks)

# Introduction

Simple and easy to use background tasks in Django without dependencies!

## Features

* ⚡ **Easy background task creation**
* 🛤️ **Multiple queue support**
* 🔄 **Automatic task retrying**
* 🛠️ **Well integrated with your chosen database**
* 🚫 **No additional dependencies**
* 🔀 **Supports both sync and async functions**

## Documentation

[🙂 Click HERE ](https://lukas346.github.io/django_firefly_tasks/)

## Instalation

```bash
pip install django_firefly_tasks
```

## Setup
settings.py
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    ###############
    'django_firefly_tasks',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },

    'loggers': {
        'django_firefly_tasks': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Quick Start
**views.py**
```python
from django.http.response import JsonResponse, Http404

from django_firefly_tasks.models import TaskModel
from django_firefly_tasks.decorators import task
from django_firefly_tasks.utils import task_as_dict


@task(queue="default", max_retries=0, retry_delay=0)
# param "queue" defines the queue in which the task will be placed
# param "max_retries" defines max retries on fail
# param "retry_delay" defines delay in seconds  between restarts
def add(i: int, j: int) -> int:
    return i + j


def task_view(request):
    """
    Example response
    ---
    {
        "id": 1,
        "func_name": "app.views.add",
        "status": "created",
        "not_before": null,
        "created": "2025-04-27T17:28:36.109Z",
        "retry_attempts": 0,
        "retry_delay": "0s",
        "max_retries": 0
    }
    """
    # pass function args to schedule method
    task = add.schedule(1, 3)
    return JsonResponse(task_as_dict(task))


def task_detail_view(request, task_id):
    """
    Example response
    ---
        4
    """
    try:
        task = TaskModel.objects.get(pk=task_id)
    except TaskModel.DoesNotExist:
        raise Http404("Task does not exist")
    # task.returned stores function returned data 
    return JsonResponse(task.returned, safe=False)
```
**urls.py**
```python
from django.urls import path

from .views import task_view, task_detail_view

urlpatterns = [
    path('task/', task_view, name='task_view'),
    path('task/<int:task_id>', task_detail_view, name='task_detail_view'),
]
```

Finally, run consumer. Default queue is called "default". **Consumer doesn't have  auto-reload, so when tasks changed it requires manual restart.**
```bash
./manage.py consume_tasks
```

## Frequently Asked Questions
### Consumer is too slow, what can I do?
Set in your `settings.py` `CONSUMER_NAP_TIME` lower value (default `0.001` aka 1000 tasks per second). You can also try to scale it horizontally by defining multiple queues and running multiple consumers for each one.
### Can I run multiple consumers for the same queue?
Yes, but it is not recommended. Consumers could lock each other.
### I changed the location or name of a decorated function, and now the consumer can't process old tasks. What should I do?
When task metadata is created, it stores the function's location in dot notation (e.g., app.views.foo). If you move or rename the function, this path changes, and the consumer can no longer locate it.

The best solution for now is to manually update the `TaskModel.func_name` field in the database to reflect the new function path - for example, change it from `app.views.foo` to `app.tasks.foo`.
### Can I specify the date and time of task execution?
This feature is coming soon.

## Support

If this project was useful to you, [feel free to buy me a coffee ☕](https://www.paypal.com/donate/?hosted_button_id=Q7LLNBFFFY57Q). It doesn't have to be from Starbucks — even a budget one is just fine ;) Every donation, no matter how small, is a sign that what I’m doing is valuable to you and worth maintaining.

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=Q7LLNBFFFY57Q)

## Contact
If you're missing something, feel free to add your own Issue or PR, which are, of course, welcome.
