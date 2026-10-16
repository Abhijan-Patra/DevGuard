"""Scheduling/cancellation evidence; no model weights or accuracy claims."""

import asyncio
import json

import httpx
import pytest

from devguard.config import Settings
from devguard.models.ollama import ModelUnavailable, OllamaClient
from devguard.models.queue import InferenceQueue, QueueUnavailable


def test_foreground_overtakes_pending_repairs_but_not_active_call_and_fifo_is_kept():
    async def run():
        queue = InferenceQueue()
        started, release = asyncio.Event(), asyncio.Event()
        order = []

        async def active():
            async with queue.slot("background"):
                order.append("active")
                started.set()
                await release.wait()

        async def work(name, priority):
            async with queue.slot(priority):
                order.append(name)

        first = asyncio.create_task(active())
        await started.wait()
        tasks = [asyncio.create_task(work("repair-1", "background")),
                 asyncio.create_task(work("repair-2", "background")),
                 asyncio.create_task(work("privacy-1", "foreground")),
                 asyncio.create_task(work("privacy-2", "foreground"))]
        await asyncio.sleep(0)
        assert queue.status()["foreground_waiting"] == 2
        assert order == ["active"]
        release.set()
        await asyncio.gather(first, *tasks)
        assert order == ["active", "privacy-1", "privacy-2", "repair-1", "repair-2"]
    asyncio.run(run())


def test_cancelled_waiter_and_active_work_release_capacity():
    async def run():
        queue = InferenceQueue(capacity=1)
        async with queue.slot("background"):
            async def waiting():
                async with queue.slot("foreground"):
                    pytest.fail("Canceled waiting work executed")
            task = asyncio.create_task(waiting())
            await asyncio.sleep(0)
            with pytest.raises(QueueUnavailable):
                async with queue.slot("foreground"):
                    pass
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert queue.status()["foreground_waiting"] == 0
        started = asyncio.Event()
        async def canceled_active():
            async with queue.slot("background"):
                started.set()
                await asyncio.Event().wait()
        active = asyncio.create_task(canceled_active())
        await started.wait()
        active.cancel()
        with pytest.raises(asyncio.CancelledError):
            await active
        async with queue.slot("foreground"):
            assert queue.status()["active"]
        assert not queue.status()["active"]
    asyncio.run(run())


def test_closing_queue_rejects_waiting_and_future_calls():
    async def run():
        queue = InferenceQueue()
        async with queue.slot("background"):
            async def wait():
                async with queue.slot("foreground"):
                    pytest.fail("Closed queue admitted work")
            task = asyncio.create_task(wait())
            await asyncio.sleep(0)
            await queue.close()
            with pytest.raises(QueueUnavailable):
                await task
        with pytest.raises(QueueUnavailable):
            async with queue.slot("background"):
                pass
        assert queue.status()["foreground_waiting"] == 0
    asyncio.run(run())


def test_http_calls_use_one_queue_and_canceled_waiter_never_reaches_ollama():
    async def run():
        active, release = asyncio.Event(), asyncio.Event()
        received = []
        async def transport(request):
            name = json.loads(request.content)["messages"][0]["content"]
            received.append(name)
            if name == "active":
                active.set()
                await release.wait()
            return httpx.Response(200, json={"message": {"content": "synthetic"}})
        client = OllamaClient(Settings("queue-unit-test-not-a-runtime-token-12345"),
                              transport=httpx.MockTransport(transport))
        def call(name, **kwargs):
            return client.chat([{"role": "user", "content": name}], **kwargs)
        try:
            first = asyncio.create_task(call("active"))
            await active.wait()
            repair = asyncio.create_task(call("repair"))
            canceled = asyncio.create_task(call("canceled", priority="foreground"))
            privacy = asyncio.create_task(call("privacy", priority="foreground"))
            await asyncio.sleep(0)
            canceled.cancel()
            with pytest.raises(asyncio.CancelledError):
                await canceled
            release.set()
            await asyncio.gather(first, repair, privacy)
            assert received == ["active", "privacy", "repair"]
        finally:
            await client.close()
        with pytest.raises(ModelUnavailable):
            await call("after-close")
    asyncio.run(run())


def test_client_shutdown_cancels_active_and_waiting_inference():
    async def run():
        entered=asyncio.Event()
        async def transport(request):
            entered.set()
            await asyncio.Event().wait()
        client=OllamaClient(Settings('shutdown-test-only-not-runtime-token-123456'),
                            transport=httpx.MockTransport(transport))
        active=asyncio.create_task(client.chat([{'role':'user','content':'synthetic'}]))
        await entered.wait()
        waiting=asyncio.create_task(client.chat([{'role':'user','content':'synthetic'}],priority='foreground'))
        await asyncio.sleep(0)
        await client.close()
        assert active.cancelled() and waiting.cancelled()
        assert not client._calls and not client.queue.status()['active']
        assert client.queue.status()['foreground_waiting']==0
    asyncio.run(run())
