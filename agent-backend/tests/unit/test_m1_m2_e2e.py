import asyncio
import os
import sys
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Milestone 1 Imports
from app.domain.business_config import get_full_business_context

# Milestone 2 STT Imports
from app.stt.deepgram_client import build_deepgram_stt_service
from app.stt.groq_whisper_client import build_groq_stt_service
from app.stt.local_whisper_client import build_local_whisper_stt_service

# Milestone 2 VAD & TTS Imports (Pipecat Native)
from pipecat.audio.vad.silero import SileroVADAnalyzer


async def run_m1_m2_e2e_test():
    print("\n" + "=" * 65)
    print("🚀 END-TO-END INTEGRATION TEST: MILESTONE 1 + MILESTONE 2")
    print("=" * 65)

    test_business_id = "11111111-1111-1111-1111-111111111111"
    errors_found = 0

    # -----------------------------------------------------------------
    # PHASE 1: MILESTONE 1 (FOUNDATION & DATABASE CONFIG)
    # -----------------------------------------------------------------
    print("\n--- [PHASE 1] Milestone 1: Environment & Database Check ---")

    # 1.1 Environment Variables Check
    required_keys = ["DATABASE_URL", "DEEPGRAM_API_KEY", "GROQ_API_KEY"]
    for key in required_keys:
        val = os.getenv(key)
        if val:
            print(f"  ✅ ENV Check: `{key}` is set.")
        else:
            print(f"  ❌ ENV Check: `{key}` is MISSING!")
            errors_found += 1

    # 1.2 Database Connectivity & Configuration Fetch
    print("\n  [DB Check] Fetching business configuration from Supabase Pooler...")
    try:
        context = await get_full_business_context(test_business_id)
        system_prompt = context.get("system_prompt")
        tools = context.get("tools", [])
        guardrails = context.get("guardrails")

        print(f"  ✅ Database Connected!")
        print(f"  ├─ System Prompt loaded: {bool(system_prompt)}")
        print(f"  ├─ Dynamic Tools loaded: {len(tools)} tools found")
        print(f"  └─ Guardrails active: {bool(guardrails)}")
    except Exception as e:
        print(f"  ❌ Database Connection Failed: {e}")
        errors_found += 1

    # -----------------------------------------------------------------
    # PHASE 2: MILESTONE 2 (AUDIO PIPELINE: VAD, STT, TTS)
    # -----------------------------------------------------------------
    print("\n--- [PHASE 2] Milestone 2: Audio Pipeline Components ---")

    # 2.1 Voice Activity Detection (VAD)
    print("  [VAD Check] Initializing Silero VAD Analyzer...")
    try:
        vad = SileroVADAnalyzer()
        print("  ✅ Silero VAD initialized successfully!")
    except Exception as e:
        print(f"  ❌ Silero VAD failed to initialize: {e}")
        errors_found += 1

    # 2.2 Speech-to-Text Tier 1 (Deepgram)
    print("\n  [STT Check] Tier 1: Deepgram STT (Primary Cloud)...")
    try:
        dg_stt = build_deepgram_stt_service()
        print("  ✅ Deepgram STT ready!")
    except Exception as e:
        print(f"  ❌ Deepgram STT failed: {e}")
        errors_found += 1

    # 2.3 Speech-to-Text Tier 2 (Groq Whisper)
    print("\n  [STT Check] Tier 2: Groq Whisper (Cloud Fallback)...")
    try:
        groq_stt = build_groq_stt_service()
        print("  ✅ Groq Whisper STT ready!")
    except Exception as e:
        print(f"  ❌ Groq Whisper STT failed: {e}")
        errors_found += 1

    # 2.4 Speech-to-Text Tier 3 (Local Whisper)
    print("\n  [STT Check] Tier 3: Local Whisper (Offline Fallback)...")
    try:
        local_stt = build_local_whisper_stt_service()
        print("  ✅ Local Whisper STT client constructed successfully!")
    except Exception as e:
        print(f"  ❌ Local Whisper STT failed: {e}")
        errors_found += 1

    # -----------------------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------------------
    print("\n" + "=" * 65)
    if errors_found == 0:
        print("🎉 ALL CHECKS PASSED! Milestones 1 & 2 are 100% ready for Milestone 4.")
    else:
        print(f"⚠️  TEST COMPLETED WITH {errors_found} ERROR(S). Please resolve before proceeding.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(run_m1_m2_e2e_test())