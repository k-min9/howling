from voicevox import Client
import asyncio

async def voicevox_tts(text, speed=1.0):
    """
    VOICEVOX를 사용한 텍스트 음성 변환
    
    Args:
        text (str): 변환할 텍스트
        speed (float): 재생 속도 (1.0=보통, 0.5=느림, 1.5=빠름)
    
    Returns:
        str: 생성된 오디오 파일 경로
    """
    import time
    async with Client() as client:
        audio_query = await client.create_audio_query(text , speaker=1)
        
        # 속도 조절
        audio_query.speed_scale = speed
        
        # voice 폴더 확인 및 생성
        import os
        if not os.path.exists('./voice'):
            os.makedirs('./voice')
        
        # 타임스탬프를 이용해 매번 다른 파일명 생성
        timestamp = str(int(time.time() * 1000))
        output_file = f"./voice/voice_{timestamp}.wav"
        with open(output_file, "wb") as f:
            f.write(await audio_query.synthesis(speaker=1))
        return output_file


if __name__ == "__main__":
    import pygame
    import os
    import time
    
    # pygame 초기화
    pygame.mixer.init()
    
    def play_and_cleanup(file_path):
        """pygame으로 오디오 재생 및 파일 정리"""
        try:
            print(f"재생 중: {file_path}")
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # 재생 완료까지 대기
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            pygame.mixer.music.unload()
            
            # 파일 정리
            if os.path.exists(file_path):
                os.remove(file_path)
                print("재생 완료 및 파일 정리됨")
                
        except Exception as e:
            print(f"재생 실패: {e}")
    
    # 테스트 실행 - 다양한 속도로 테스트
    test_text = "これから答えを短くしてください。"
    test_speeds = [
        (0.8, "느린 속도"),
        (1.0, "보통 속도"), 
        (1.3, "빠른 속도")
    ]
    
    for speed, description in test_speeds:
        print(f"\nVOICEVOX TTS 테스트 - {description} ({speed}x): {test_text}")
        
        try:
            result = asyncio.run(voicevox_tts(test_text, speed=speed))
            print(f"생성된 파일: {result}")
            play_and_cleanup(result)
        except Exception as e:
            print(f"TTS 실행 실패: {e}")
    
    print("\n모든 속도 테스트 완료!")