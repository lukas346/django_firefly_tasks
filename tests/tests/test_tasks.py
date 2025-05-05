from unittest.mock import patch

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
    broken_async_add,
    broken_sync_add,
    create_foo,
    create_foo_failling,
    failling,
    restarting_failling,
)


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


class AsyncTasksTest(TestCase):
    def test_atask_simple(self):
        task = async_add.schedule(1, 3)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_add")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        self.assertEqual(task.returned, 4)

    def test_task_async_not_supported(self):
        with self.assertRaises(SyncFuncNotSupportedException):
            broken_async_add.schedule(1, 3)

    def test_model_task_simple(self):
        name = "FooBar"

        task = async_create_foo.schedule(name)

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        foo = FooModel.objects.get(name=name)

        self.assertTrue(foo)

    def test_failing_task(self):
        task = async_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        task.is_postponed = lambda: False

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

    def test_failing_restarting_task(self):
        task = async_restarting_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RETRIES):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    def test_failing_restarting_finally_succeed_task(self):
        task = async_restarting_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        for _ in range(settings.MAX_RETRIES - 1):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES - 1)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

        task.is_postponed = lambda: False

        with patch("tests.tasks.failing_func"):
            with transaction.atomic():
                task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_restarting_failling")
        self.assertEqual(task.status, Status.COMPLETED)
        self.assertEqual(task.retry_attempts, settings.MAX_RETRIES - 1)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, settings.MAX_RETRIES)

    def test_model_failling_task(self):
        task = async_create_foo_failling.schedule()

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo_failling")
        self.assertEqual(task.status, Status.CREATED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        with transaction.atomic():
            task_processor(task)

        task = TaskModel.objects.get(pk=task.pk)

        self.assertEqual(task.func_name, "tests.tasks.async_create_foo_failling")
        self.assertEqual(task.status, Status.FAILED)
        self.assertEqual(task.retry_attempts, 0)
        self.assertEqual(task.retry_delay, settings.RETRY_DELAY)
        self.assertEqual(task.max_retries, 0)

        self.assertEqual(FooModel.objects.count(), 0)
