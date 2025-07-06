# Howling

## 개요

- 입력한 음성을 일본어, 한국어, 영어 TTS(Text-to-Speech) 프로젝트
  - 기본 gTTS. 일본어는 VOICEVOX 우선 사용, 실패할 경우 gTTS로 대체

## 환경 세팅

- VOICEVOX ENGINE : <https://github.com/VOICEVOX/voicevox_engine/releases>
- venv, library 세팅
- 가상환경 및 라이브러리 설치

    ```bash
    # 가상환경 생성
    py -3.10 -m venv venv
    source venv/Scripts/Activate

    # 설치
    pip install gTTS
    pip install pyinstaller
    pip install voicevox-client
    pip install pygame

    pip install requests
    pip install Flask
    pip install waitress  # WSGI for production

    ```

## 빌드

- pyinstaller 빌드
- pyinstaller --onedir server_interface.py -n howling_server --contents-directory=files_howling --noconfirm  # Flask 버전
