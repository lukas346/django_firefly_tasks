import asyncio

from django_simple_tasks.decorators import task, atask

from django.conf import settings
from tests.models import FooModel


@task(queue=settings.DEFAULT_QUEUE, max_restarts=settings.MAX_RESTARTS, restart_delay=settings.RESTART_DELAY)
def add(i: int, j: int) -> int:
    return i + j

@atask(queue=settings.DEFAULT_QUEUE, max_restarts=settings.MAX_RESTARTS, restart_delay=settings.RESTART_DELAY)
async def async_add(i: int, j: int) -> int:
    await asyncio.sleep(0.0001)
    return i + j

@task()
def create_foo(name: str) -> FooModel:
    return FooModel.objects.create(name=name)

@atask()
async def async_create_foo(name: str) -> FooModel:
    return await FooModel.objects.acreate(name=name)

@task(queue=settings.DEFAULT_QUEUE, max_restarts=0, restart_delay=settings.RESTART_DELAY)
def failling():
    raise Exception

@atask(queue=settings.DEFAULT_QUEUE, max_restarts=0, restart_delay=settings.RESTART_DELAY)
async def async_failling():
    await asyncio.sleep(0.0001)
    raise Exception

@task(queue=settings.DEFAULT_QUEUE, max_restarts=settings.MAX_RESTARTS, restart_delay=settings.RESTART_DELAY)
def restarting_failling():
    raise Exception

@atask(queue=settings.DEFAULT_QUEUE, max_restarts=settings.MAX_RESTARTS, restart_delay=settings.RESTART_DELAY)
async def async_restarting_failling():
    await asyncio.sleep(0.0001)
    raise Exception
