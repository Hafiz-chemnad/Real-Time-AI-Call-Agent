from typing import Callable, Optional
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams

async def run_with_tts_fallback(
    tts_service_getters: list,
    upstream_processors: list,
    downstream_processors: list,
    on_task_created: Optional[Callable[[PipelineTask], None]] = None,
    is_resume: bool = False,
):
    """
    tts_service_getters: list of functions like get_primary_tts_service,
    get_fallback_tts_service, get_local_tts_service — called lazily, one at
    a time, so we don't even initialize Tier 2/3 unless Tier 1 fails.

    IMPORTANT: only the FIRST tts tier attempt is allowed to retry with a
    fresh Pipeline. If the pipeline starts running and then fails partway
    through (not just at TTS init), the STT service and other upstream
    processors have already been started once — reusing them in a second
    Pipeline() can leave them in an inconsistent state. So once a pipeline
    has actually started running, further failures are raised, not retried.

    on_task_created: optional callback fired with the real PipelineTask
    right after it's constructed, before the pipeline actually starts
    running. Lets the caller wire up a reference to the task on any
    processor that needs to be able to stop the pipeline directly (e.g.
    Milestone1BrainProcessor calling task.cancel() to trigger a language-
    switch rebuild) — task.cancel() is the only mechanism confirmed to
    actually make runner.run(task) return; a bare push_frame(CancelFrame())
    was tested and found to hang indefinitely instead.
    """
    last_error = None
    started_once = False

    for i, get_service in enumerate(tts_service_getters):
        service = get_service()
        if service is None:
            continue

        if started_once:
            raise RuntimeError(
                f"Pipeline already started once and failed; not retrying "
                f"with tier {i}. Last error: {last_error}"
            )

        try:
            pipeline = Pipeline([*upstream_processors, service, *downstream_processors])
            task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))

            if on_task_created is not None:
                on_task_created(task)

            runner = PipelineRunner()
            started_once = True
            await runner.run(task)
            return
        except Exception as exc:
            last_error = exc
            print(f"TTS tier {i} failed: {exc}, trying next tier...")
            continue

    raise RuntimeError(f"All TTS tiers failed. Last error: {last_error}")