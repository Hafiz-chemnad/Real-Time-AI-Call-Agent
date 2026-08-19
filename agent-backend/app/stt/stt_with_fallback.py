# app/stt/stt_with_fallback.py
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams


async def run_with_stt_fallback(stt_service_getters: list, upstream_processors: list, downstream_processors: list):
    """
    stt_service_getters: list of functions like build_deepgram_stt_service,
    build_groq_stt_service, build_local_whisper_stt_service — called lazily,
    one at a time, so we don't initialize Tier 2/3 unless Tier 1 fails.
    """
    last_error = None
    for i, get_service in enumerate(stt_service_getters):
        try:
            service = get_service()
        except Exception as exc:
            # e.g. missing API key raised inside the getter itself
            last_error = exc
            print(f"STT tier {i} failed to initialize: {exc}, trying next tier...")
            continue

        try:
            pipeline = Pipeline([*upstream_processors, service, *downstream_processors])
            task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
            runner = PipelineRunner()
            await runner.run(task)
            return  # this tier succeeded — done
        except Exception as exc:
            last_error = exc
            print(f"STT tier {i} ({type(service).__name__}) failed: {exc}, trying next tier...")
            continue

    raise RuntimeError(f"All STT tiers failed. Last error: {last_error}")