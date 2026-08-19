# app/tts/tts_with_fallback.py
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams


async def run_with_tts_fallback(tts_service_getters: list, upstream_processors: list, downstream_processors: list):
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
    """
    last_error = None
    started_once = False

    for i, get_service in enumerate(tts_service_getters):
        service = get_service()
        if service is None:
            continue  # tier failed to init (missing key, etc.) — skip

        if started_once:
            # A previous tier's pipeline already started running upstream
            # processors (STT, VAD, etc.) before failing. Reusing them now
            # would be unsafe — surface the original error instead of
            # silently retrying with stale state.
            raise RuntimeError(
                f"Pipeline already started once and failed; not retrying "
                f"with tier {i} to avoid reusing stale upstream processors. "
                f"Last error: {last_error}"
            )

        try:
            pipeline = Pipeline([*upstream_processors, service, *downstream_processors])
            task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
            runner = PipelineRunner()
            started_once = True
            await runner.run(task)
            return  # this tier succeeded — done
        except Exception as exc:
            last_error = exc
            print(f"TTS tier {i} ({type(service).__name__}) failed: {exc}, trying next tier...")
            continue

    raise RuntimeError(f"All TTS tiers failed. Last error: {last_error}")