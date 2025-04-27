
# Global Configuration

You can customize the behavior of Django FireFly Tasks by editing `settings.py`.

## `settings.DEFAULT_QUEUE`
Defines the global default queue name. Default: `default`.

## `settings.MAX_RETRIES`
Defines the global maximum number of retries. Default: `0`.

## `settings.RETRY_DELAY`
Defines the global retry delay (in seconds). Default: `120`.

## `settings.CONSUMER_NAP_TIME`
Defines the consumer sleep time (in seconds) between each task. Default: `0.001`.