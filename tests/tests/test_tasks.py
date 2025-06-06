from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from django.test import TestCase

from django_firefly_tasks._private.processors import task_processor
from django_firefly_tasks.exceptions import (
    AsyncFuncNotSupportedException,
    SyncFuncNotSupportedException,
)
from django_firefly_tasks.models import Status, TaskModel
from tests.models import FooModel
from tests.tasks import (
    add,
    async_add,
    async_create_foo,
    async_create_foo_failling,
    async_failling,
    async_restarting_failling,
    async_schedule_task,
    broken_async_add,
    broken_sync_add,
    create_foo,
    create_foo_failling,
    failling,
    restarting_failling,
    schedule_task,
)


def process(task):
    with transaction.atomic():
        task_processor(task)


class TasksTest(TestCase):
    def test_task_simple(self):
        task = add.schedule(1, 3)

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        self.assertEqual(task.returned, 4)

    def test_task_simple_eta_passed(self):
        eta = datetime(2025, 3, 30, 18, 30, tzinfo=ZoneInfo("UTC"))
        task = add.schedule(1, 3, eta=eta)

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with patch("django_firefly_tasks.models.timezone.now", return_value=eta + timedelta(hours=3)):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        self.assertEqual(task.returned, 4)

    def test_task_simple_eta_not_yet(self):
        eta = datetime(2025, 3, 30, 18, 30, tzinfo=ZoneInfo("UTC"))
        task = add.schedule(1, 3, eta=eta)

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with patch("django_firefly_tasks.models.timezone.now", return_value=eta - timedelta(hours=3)):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    def test_task_eta_failed_then_succeed(self):
        eta = datetime(2025, 3, 30, 18, 30, tzinfo=ZoneInfo("UTC"))
        task = restarting_failling.schedule(eta=eta)

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.not_before, eta)

        with patch("django_firefly_tasks.models.timezone.now", return_value=eta + timedelta(hours=3)):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 1)
        self.assertEqual(task.not_before, eta + timedelta(hours=3) + timedelta(seconds=settings.RETRY_DELAY))

        with patch(
            "django_firefly_tasks.models.timezone.now",
            return_value=eta + timedelta(hours=3) + timedelta(seconds=settings.RETRY_DELAY),
        ):
            with patch("tests.tasks.failing_func"):
                with transaction.atomic():
                    task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 1)
        self.assertEqual(task.not_before, eta + timedelta(hours=3) + timedelta(seconds=settings.RETRY_DELAY))

    def test_task_sync_not_supported(self):
        with self.assertRaises(AsyncFuncNotSupportedException):
            broken_sync_add.schedule(1, 3)

    def test_model_task_simple(self):
        name = "FooBar"

        task = create_foo.schedule(name)

        self.assertEqual(task.func_name, "tests.tasks.create_foo")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.create_foo")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        foo = FooModel.objects.get(name=name)

        self.assertTrue(foo)

    def test_model_failling_task(self):
        task = create_foo_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.create_foo_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.create_foo_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        self.assertEqual(FooModel.objects.count(), 0)

    def test_failing_task(self):
        task = failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        task.is_postponed = lambda: False

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

    def test_failing_restarting_task(self):
        task = restarting_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RETRIES):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    def test_failing_restarting_finally_succeed_task(self):
        task = restarting_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RETRIES - 1):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES - 1)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        with patch("tests.tasks.failing_func"):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.restarting_failling")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES - 1)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    def test_schedule_task_inside_task(self):
        task = schedule_task.schedule()

        self.assertEqual(task.func_name, "tests.tasks.schedule_task")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(func_name="tests.tasks.add")

        self.assertEqual(task.func_name, "tests.tasks.add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)


class AsyncTasksTest(TestCase):
    async def test_atask_simple(self):
        task = await async_add.schedule(1, 3)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        self.assertEqual(task.returned, 4)

    async def test_task_simple_eta_passed(self):
        eta = datetime(2025, 3, 30, 18, 30, tzinfo=ZoneInfo("UTC"))
        task = await async_add.schedule(1, 3, eta=eta)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with patch("django_firefly_tasks.models.timezone.now", return_value=eta + timedelta(hours=3)):
            await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        self.assertEqual(task.returned, 4)

    async def test_task_simple_eta_not_yet(self):
        eta = datetime(2025, 3, 30, 18, 30, tzinfo=ZoneInfo("UTC"))
        task = await async_add.schedule(1, 3, eta=eta)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with patch("django_firefly_tasks.models.timezone.now", return_value=eta - timedelta(hours=3)):
            await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    async def test_task_eta_failed_then_succeed(self):
        eta = datetime(2025, 3, 30, 18, 30, tzinfo=ZoneInfo("UTC"))
        task = await async_restarting_failling.schedule(eta=eta)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.not_before, eta)

        with patch("django_firefly_tasks.models.timezone.now", return_value=eta + timedelta(hours=3)):
            await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 1)
        self.assertEqual(task.not_before, eta + timedelta(hours=3) + timedelta(seconds=settings.RETRY_DELAY))

        with patch(
            "django_firefly_tasks.models.timezone.now",
            return_value=eta + timedelta(hours=3) + timedelta(seconds=settings.RETRY_DELAY),
        ):
            with patch("tests.tasks.failing_func"):
                await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 1)
        self.assertEqual(task.not_before, eta + timedelta(hours=3) + timedelta(seconds=settings.RETRY_DELAY))

    async def test_task_async_not_supported(self):
        with self.assertRaises(SyncFuncNotSupportedException):
            await broken_async_add.schedule(1, 3)

    async def test_model_task_simple(self):
        name = "FooBar"

        task = await async_create_foo.schedule(name)

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        foo = await FooModel.objects.aget(name=name)

        self.assertTrue(foo)

    async def test_failing_task(self):
        task = await async_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        task.is_postponed = lambda: False

        await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

    async def test_failing_restarting_task(self):
        task = await async_restarting_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RETRIES):
            await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    async def test_failing_restarting_finally_succeed_task(self):
        task = await async_restarting_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RETRIES - 1):
            await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES - 1)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        with patch("tests.tasks.failing_func"):
            await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES - 1)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    async def test_model_failling_task(self):
        task = await async_create_foo_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        self.assertEqual(await FooModel.objects.acount(), 0)

    async def test_schedule_task_inside_task(self):
        task = await async_schedule_task.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_schedule_task")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        await sync_to_async(process)(task)

        task = await TaskModel.objects.aget(func_name="tests.tasks.async_add")

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)
