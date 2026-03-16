import asyncio
import inspect
import traceback
from typing import Callable


class BackgroundTaskRunner:
    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    def add(self, fn: Callable, *args, **kwargs):
        loop = asyncio.get_event_loop()

        async def _run():
            try:
                if inspect.iscoroutinefunction(fn):
                    await fn(*args, **kwargs)
                else:
                    await loop.run_in_executor(None, lambda: fn(*args, **kwargs))
            except Exception:
                traceback.print_exc()

        task = loop.create_task(_run())
        self._tasks.append(task)
        task.add_done_callback(lambda t: self._tasks.remove(t) if t in self._tasks else None)

    async def wait(self):
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    def __repr__(self):
        return f"<BackgroundTaskRunner pending={len(self._tasks)}>"


class BackgroundTasks:
    def __init__(self):
        self._fns: list[tuple[Callable, tuple, dict]] = []

    def add(self, fn: Callable, *args, **kwargs):
        self._fns.append((fn, args, kwargs))

    async def run_all(self):
        runner = BackgroundTaskRunner()
        for fn, args, kwargs in self._fns:
            runner.add(fn, *args, **kwargs)
        await runner.wait()