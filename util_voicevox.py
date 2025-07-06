from voicevox import Client
import asyncio

async def voicevox_tts(text):
    import time
    async with Client() as client:
        audio_query = await client.create_audio_query(text , speaker=1)
        # 타임스탬프를 이용해 매번 다른 파일명 생성
        timestamp = str(int(time.time() * 1000))
        output_file = f"voice_{timestamp}.wav"
        with open(output_file, "wb") as f:
            f.write(await audio_query.synthesis(speaker=1))
        return output_file


if __name__ == "__main__":
    ## already in asyncio (in a Jupyter notebook, for example)
    # await main()
    ## otherwise
    text = "これから答えを短くしてください。"
    asyncio.run(voicevox_tts(text))