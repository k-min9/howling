from gtts import gTTS
import time
import os

def gtts_tts(text, lang='auto'):
    """
    gTTS를 사용한 텍스트 음성 변환
    
    Args:
        text (str): 변환할 텍스트
        lang (str): 언어 코드 ('auto', 'ko', 'en', 'ja' 등)
    
    Returns:
        str: 생성된 오디오 파일 경로
    """
    # 언어 자동 감지
    if lang == 'auto':
        lang = detect_language_for_gtts(text)
    
    # voice 폴더 확인 및 생성
    if not os.path.exists('./voice'):
        os.makedirs('./voice')
    
    # 타임스탬프를 이용해 매번 다른 파일명 생성
    timestamp = str(int(time.time() * 1000))
    output_file = f"./voice/gtts_{timestamp}.mp3"
    
    try:
        # gTTS 객체 생성 및 파일 저장
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_file)
        return output_file
    except Exception as e:
        # 오류 발생 시 예외 발생
        raise Exception(f"gTTS 실행 실패: {str(e)}")

def detect_language_for_gtts(text):
    """
    gTTS용 언어 감지 (server_interface.py의 detect_language와 동일)
    
    Args:
        text (str): 분석할 텍스트
    
    Returns:
        str: gTTS 언어 코드 ('ko', 'ja', 'en')
    """
    import re
    
    korean_pattern = re.compile(r'[\uac00-\ud7a3]')
    japanese_pattern = re.compile(r'[\u3040-\u30ff\u31f0-\u31ff\u4e00-\u9faf]')

    korean_count = len(korean_pattern.findall(text))
    japanese_count = len(japanese_pattern.findall(text))

    if japanese_count > korean_count and japanese_count > 0:
        return "ja"
    elif korean_count > 0:
        return "ko"
    else:
        return "en"

if __name__ == "__main__":
    import pygame
    
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
    
    # 테스트 실행
    test_texts = [
        "안녕하세요",
        "Hello World", 
        "こんにちは"
    ]
    
    for text in test_texts:
        try:
            # 언어 감지
            detected_lang = detect_language_for_gtts(text)
            lang_names = {'ko': '한국어', 'ja': '일본어', 'en': '영어'}
            lang_name = lang_names.get(detected_lang, detected_lang)
            
            print(f"\ngTTS 테스트: {text}")
            print(f"감지된 언어: {lang_name} ({detected_lang})")
            
            result = gtts_tts(text)
            print(f"생성된 파일: {result}")
            play_and_cleanup(result)
            
        except Exception as e:
            print(f"오류: {e}")
    
    print("\n모든 테스트 완료!") 