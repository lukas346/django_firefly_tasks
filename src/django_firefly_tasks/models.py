from datetime import timedelta

from django.db import models
from django.utils import timezone

from ._private.utils import deserialize_object


class Status(models.TextChoices):
    CREATED = "created"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskModel(models.Model):
    # func name with path in dot notation
    func_name = models.CharField(max_length=400)
    # target queue
    queue = models.CharField(max_length=400)
    status = models.CharField(choices=Status.choices, default=Status.CREATED, max_length=400)

    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(null=True, blank=True)
    failed = models.DateTimeField(null=True, blank=True)
    # data before functions cannot be executed.
    not_before = models.DateTimeField(null=True, blank=True)

    # serialized params to base64
    raw_params = models.TextField(null=True, blank=True)
    # serialized returned data to base64
    raw_returned = models.TextField(null=True, blank=True)

    retry_attempts = models.IntegerField(default=0)
    # delay in seconds between restarts
    retry_delay = models.IntegerField(default=0)
    # max retries on fail
    max_retries = models.IntegerField()

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    @property
    def params(self):
        if not self.raw_params:
            return

        return deserialize_object(self.raw_params)

    @property
    def returned(self):
        if not self.raw_returned:
            return

        return deserialize_object(self.raw_returned)

    def set_as_failed(self):
        self.status = Status.FAILED
        self.failed = timezone.now()

    def set_as_completed(self):
        self.status = Status.COMPLETED
        self.completed = timezone.now()

    def can_be_restarted(self) -> bool:
        return self.max_retries > 0 and self.retry_attempts < self.max_retries

    def is_postponed(self) -> bool:
        return self.not_before and timezone.now() < self.not_before

    def setup_for_restart(self):
        self.retry_attempts += +1
        self.not_before = timezone.now() + timedelta(seconds=self.retry_delay)
