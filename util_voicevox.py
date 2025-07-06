try:
    from vvclient import Client
except:
    # product 단계에서는 없어도 지장 없음
    pass

import asyncio

async def voicevox_tts(text):
    async with Client() as client:
        audio_query = await client.create_audio_query(text , speaker=1)
        with open("voice.wav", "wb") as f:
            f.write(await audio_query.synthesis(speaker=1))


if __name__ == "__main__":
    ## already in asyncio (in a Jupyter notebook, for example)
    # await main()
    ## otherwise
    text = "これから答えを短くしてください。"
    asyncio.run(voicevox_tts(text))