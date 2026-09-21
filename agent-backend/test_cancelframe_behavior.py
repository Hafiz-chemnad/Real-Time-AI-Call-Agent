# test_cancelframe_behavior.py — updated to test the real cancellation path
import asyncio
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import TextFrame
from pipecat.processors.frame_processor import FrameProcessor

class TriggerCancel(FrameProcessor):
    def __init__(self, task_ref_holder: dict):
        super().__init__()
        self.task_ref_holder = task_ref_holder

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            print("Calling task.cancel() now...")
            await self.task_ref_holder["task"].cancel()
            return
        await self.push_frame(frame, direction)

async def main():
    task_ref_holder = {}
    pipeline = Pipeline([TriggerCancel(task_ref_holder)])
    task = PipelineTask(pipeline)
    task_ref_holder["task"] = task
    runner = PipelineRunner()

    async def send():
        await asyncio.sleep(1)
        await task.queue_frame(TextFrame(text="trigger"))

    asyncio.create_task(send())

    try:
        await asyncio.wait_for(runner.run(task), timeout=5)
        print("✅ runner.run() RETURNED NORMALLY")
    except asyncio.TimeoutError:
        print("❌ TIMED OUT — runner.run() never returned even with task.cancel()")
    except Exception as e:
        print(f"❌ runner.run() RAISED: {type(e).__name__}: {e}")

asyncio.run(main())