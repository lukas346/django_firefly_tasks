import asyncio

from django.conf import settings

from django_firefly_tasks.decorators import atask, task
from tests.models import FooModel
from tests.utils import failing_func


@task(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
def add(i: int, j: int) -> int:
    return i + j


@atask(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
async def async_add(i: int, j: int) -> int:
    await asyncio.sleep(0.0001)
    return i + j


@atask(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
def broken_async_add(i: int, j: int) -> int:
    return i + j


@task(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
async def broken_sync_add(i: int, j: int) -> int:
    return i + j


@task()
def create_foo(name: str) -> FooModel:
    return FooModel.objects.create(name=name)


@atask()
async def async_create_foo(name: str) -> FooModel:
    return await FooModel.objects.acreate(name=name)


@task(queue=settings.DEFAULT_QUEUE, max_retries=0, retry_delay=settings.RETRY_DELAY)
def failling():
    raise Exception


@atask(queue=settings.DEFAULT_QUEUE, max_retries=0, retry_delay=settings.RETRY_DELAY)
async def async_failling():
    await asyncio.sleep(0.0001)
    raise Exception


@task(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
def restarting_failling():
    failing_func()


@atask(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
async def async_restarting_failling():
    await asyncio.sleep(0.0001)
    failing_func()


@task(queue=settings.DEFAULT_QUEUE, max_retries=0, retry_delay=settings.RETRY_DELAY)
def create_foo_failling(name: str):
    FooModel.objects.create(name=name)
    raise Exception


@atask(queue=settings.DEFAULT_QUEUE, max_retries=0, retry_delay=settings.RETRY_DELAY)
async def async_create_foo_failling(name: str):
    await FooModel.objects.acreate(name=name)
    raise Exception


@task(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
def schedule_task():
    add.schedule(1, 3)


@atask(queue=settings.DEFAULT_QUEUE, max_retries=settings.MAX_RETRIES, retry_delay=settings.RETRY_DELAY)
async def async_schedule_task():
    await asyncio.sleep(0.0001)
    await async_add.schedule(1, 3)
