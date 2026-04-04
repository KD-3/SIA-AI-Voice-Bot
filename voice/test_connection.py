"""Quick test script to verify all API connections."""

import asyncio
from loguru import logger
from dotenv import load_dotenv

# Load environment
load_dotenv("../.env")

from config import settings
from pipeline import STTService, LLMService, TTSService


async def test_stt():
    """Test Deepgram connection."""
    logger.info("Testing Deepgram STT...")
    try:
        def on_transcript(text, is_final):
            logger.info(f"Transcript: {text} (final={is_final})")

        stt = STTService(on_transcript)
        await stt.connect()
        logger.success("✅ Deepgram STT: Connected")
        await stt.disconnect()
        return True
    except Exception as e:
        logger.error(f"❌ Deepgram STT: {e}")
        return False


async def test_llm():
    """Test OpenAI connection."""
    logger.info("Testing OpenAI LLM...")
    try:
        def on_response(text):
            logger.info(f"Response: {text}")

        llm = LLMService(on_response)
        llm.connect()
        response = await llm.generate_response("Hello, can you hear me?")
        logger.success(f"✅ OpenAI LLM: {response[:50]}...")
        return True
    except Exception as e:
        logger.error(f"❌ OpenAI LLM: {e}")
        return False


async def test_tts():
    """Test ElevenLabs connection."""
    logger.info("Testing ElevenLabs TTS...")
    try:
        audio_chunks = []

        def on_audio(chunk):
            audio_chunks.append(chunk)

        tts = TTSService(on_audio)
        tts.connect()
        await tts.synthesize_streaming("Hello, this is a test.")
        logger.success(f"✅ ElevenLabs TTS: Generated {len(audio_chunks)} audio chunks")
        return True
    except Exception as e:
        logger.error(f"❌ ElevenLabs TTS: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 50)
    logger.info("API Connection Tests")
    logger.info("=" * 50)

    logger.info(f"Twilio Account SID: {settings.twilio_account_sid[:10]}...")
    logger.info(f"Twilio Phone: {settings.twilio_phone_number}")
    logger.info("")

    results = {
        "Deepgram STT": await test_stt(),
        "OpenAI LLM": await test_llm(),
        "ElevenLabs TTS": await test_tts(),
    }

    logger.info("")
    logger.info("=" * 50)
    logger.info("Results Summary")
    logger.info("=" * 50)

    all_passed = True
    for service, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{service}: {status}")
        if not passed:
            all_passed = False

    logger.info("")
    if all_passed:
        logger.success("🎉 All tests passed! Ready to make phone calls.")
    else:
        logger.error("⚠️  Some tests failed. Check your .env configuration.")


if __name__ == "__main__":
    asyncio.run(main())
