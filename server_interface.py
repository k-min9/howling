import re
import tkinter as tk
import tkinter.messagebox
import subprocess
import time
import requests
import os
import threading
import asyncio
import pygame

# Server-Flask
from flask import Flask, Response, request, jsonify, send_file, abort
from waitress import serve

# Local
import util_voicevox

app = Flask(__name__)

# pygame 초기화
pygame.mixer.init()

# 전역 변수
is_listening = False
status_label = None
btn_start = None
btn_stop = None
btn_test = None

# 필요언어 체크
'''
영어, 한국어, 일본어로 분류
'''
def detect_language(text):
    korean_pattern = re.compile(r'[\uac00-\ud7a3]')
    japanese_pattern = re.compile(r'[\u3040-\u30ff\u31f0-\u31ff\u4e00-\u9faf]')

    korean_count = len(korean_pattern.findall(text))
    japanese_count = len(japanese_pattern.findall(text))

    lang = 'en'
    if japanese_count > korean_count and japanese_count > 0:
        return "ja"
    elif korean_count > 0:
        return "ko"
    
    return lang

# 한국어 텍스트를 입력받아 변환
@app.route('/howling', methods=['POST'])
def synthesize_sound():
    text = request.json.get('text', '안녕하십니까.')
    lang = request.json.get('lang', '')
    # speed = request.json.get('speed', 100)  # % 50~100
    # speed = float(speed)/100 
    
    if lang == 'ja' or lang =='jp':
        lang = 'ja'  # 단어보정
    if not lang:
        lang = detect_language(text)
    if lang not in ['ja', 'ko', 'en']:
        lang = 'en'
        
    # 일본어면 1순위로 voicevox 시도
    try:
        # 비동기 함수를 동기적으로 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(util_voicevox.voicevox_tts(text))
        loop.close()
        
        if os.path.exists(result):
            response = send_file(result, mimetype="audio/wav")
            return response
    except:
        pass
    
    # return 되지 않았다면 언어필요없이 gtts로 반환
    return jsonify({"error": "TTS 실행 실패"})
    
# VOICEVOX Engine 실행 확인 함수
def is_voicevox_running():
    """VOICEVOX Engine이 실행 중인지 확인 (50021 포트 체크)"""
    try:
        response = requests.get('http://localhost:50021/version', timeout=3)
        return response.status_code == 200
    except:
        return False

# VOICEVOX Engine 시작 대기 함수
def wait_for_voicevox(max_wait=30):
    """VOICEVOX Engine이 준비될 때까지 대기"""
    print('VOICEVOX Engine 준비 대기 중...')
    for i in range(max_wait):
        if is_voicevox_running():
            print('VOICEVOX Engine 준비 완료!')
            return True
        time.sleep(1)
        print(f'대기 중... ({i+1}/{max_wait})')
    print('VOICEVOX Engine 시작 실패 - 시간 초과')
    return False

# 상태 업데이트 함수
def update_status(message):
    """상태 라벨 업데이트"""
    if status_label:
        status_label.config(text=message)
        status_label.update()

# 오디오 재생 함수
def play_audio_file(file_path, auto_cleanup=True):
    """
    pygame을 사용하여 오디오 파일 재생
    
    Args:
        file_path (str): 재생할 오디오 파일 경로
        auto_cleanup (bool): 재생 완료 후 파일 자동 삭제 여부
    """
    if not os.path.exists(file_path):
        update_status(f"파일을 찾을 수 없습니다: {file_path}")
        tkinter.messagebox.showwarning("경고", f"파일을 찾을 수 없습니다: {file_path}")
        return
    
    try:
        # 이전 음악 정지 및 리소스 해제
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        
        # 새 파일 로드 및 재생
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        update_status(f"재생 중: {os.path.basename(file_path)}")
        
        # 재생 완료 후 파일 정리를 위한 스레드
        if auto_cleanup:
            def cleanup_file():
                # 재생이 끝날 때까지 대기
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                # 파일 정리
                try:
                    pygame.mixer.music.unload()
                    time.sleep(0.1)  # 파일 언로드 대기
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        update_status("재생 완료 및 파일 정리됨")
                except Exception as e:
                    update_status(f"파일 정리 실패: {str(e)}")
            
            cleanup_thread = threading.Thread(target=cleanup_file)
            cleanup_thread.daemon = True
            cleanup_thread.start()
        else:
            # 파일 정리 없이 재생 완료 확인만
            def wait_for_completion():
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                pygame.mixer.music.unload()
                update_status("재생 완료")
            
            wait_thread = threading.Thread(target=wait_for_completion)
            wait_thread.daemon = True
            wait_thread.start()
            
    except Exception as e:
        update_status(f"재생 실패: {str(e)}")
        tkinter.messagebox.showerror("재생 오류", f"오디오 재생 실패:\n{str(e)}")

# 서버 시작 스레드 함수
def server_start_thread():
    """서버 시작을 별도 스레드에서 실행"""
    update_status("서버 구동 시작...")
    
    # 기존 서버 체크
    if is_voicevox_running():
        update_status("기존 VOICEVOX Engine 감지됨")
    else:
        update_status("VOICEVOX Engine 시작 중...")
        
    # 서버 시작
    server_start()

# 버튼 함수들
def start_server():
    """서버시작 버튼 클릭"""
    global btn_start, btn_stop, btn_test
    
    # 다른 버튼들 활성화
    if btn_start:
        btn_start.config(state='normal')
    if btn_stop:
        btn_stop.config(state='normal') 
    if btn_test:
        btn_test.config(state='normal')
    
    # 별도 스레드에서 서버 시작
    thread = threading.Thread(target=server_start_thread)
    thread.daemon = True
    thread.start()

def start_listening():
    """시작 버튼 클릭"""
    global is_listening
    is_listening = True
    update_status("음성 인식 시작")

def stop_listening():
    """중지 버튼 클릭"""
    global is_listening
    is_listening = False
    update_status("음성 인식 중지")

def test():
    """테스트 버튼 클릭"""
    open_test_modal()

def open_test_modal():
    """테스트 모달 창 열기"""
    # 모달 창 생성
    test_window = tk.Toplevel()
    test_window.title("TTS 테스트")
    test_window.geometry("500x300")
    test_window.resizable(False, False)
    
    # 모달 설정
    test_window.transient()  # 부모 창 위에 표시
    test_window.grab_set()   # 모달 설정
    
    # 예시 버튼 프레임
    example_frame = tk.Frame(test_window)
    example_frame.pack(pady=10)
    
    # 예시 버튼들
    btn_example1 = tk.Button(example_frame, text="예시1 (한국어)", width=15)
    btn_example1.pack(side=tk.LEFT, padx=5)
    
    btn_example2 = tk.Button(example_frame, text="예시2 (영어)", width=15)
    btn_example2.pack(side=tk.LEFT, padx=5)
    
    btn_example3 = tk.Button(example_frame, text="예시3 (일본어)", width=15)
    btn_example3.pack(side=tk.LEFT, padx=5)
    
    # 입력 텍스트 영역
    text_frame = tk.Frame(test_window)
    text_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
    
    tk.Label(text_frame, text="테스트 텍스트:").pack(anchor=tk.W)
    text_entry = tk.Text(text_frame, height=8, width=50)
    text_entry.pack(fill=tk.BOTH, expand=True, pady=5)
    
    # 예시 버튼 이벤트 함수들
    def set_korean_example():
        text_entry.delete(1.0, tk.END)
        text_entry.insert(1.0, "안녕하세요")
    
    def set_english_example():
        text_entry.delete(1.0, tk.END)
        text_entry.insert(1.0, "Hello")
    
    def set_japanese_example():
        text_entry.delete(1.0, tk.END)
        text_entry.insert(1.0, "こんにちは")
    
    def run_test():
        """테스트 실행"""
        text = text_entry.get(1.0, tk.END).strip()
        if not text:
            tkinter.messagebox.showwarning("경고", "텍스트를 입력해주세요.")
            return
        
        def run_async_test():
            """비동기 테스트 실행을 별도 스레드에서 처리"""
            try:
                update_status(f"TTS 테스트 실행: {text}")
                # 새로운 이벤트 루프 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(util_voicevox.voicevox_tts(text))
                loop.close()
                
                update_status(f"TTS 테스트 완료: {result}")
                
                # 생성된 오디오 파일 재생 (자동 정리 활성화)
                play_audio_file(result, auto_cleanup=True)
                    
            except Exception as e:
                update_status(f"TTS 테스트 실패: {str(e)}")
                tkinter.messagebox.showerror("오류", f"TTS 테스트 실패:\n{str(e)}")
        
        # 별도 스레드에서 비동기 작업 실행
        thread = threading.Thread(target=run_async_test)
        thread.daemon = True
        thread.start()
    
    # 예시 버튼에 이벤트 연결
    btn_example1.config(command=set_korean_example)
    btn_example2.config(command=set_english_example)
    btn_example3.config(command=set_japanese_example)
    
    # 테스트 버튼
    test_btn_frame = tk.Frame(test_window)
    test_btn_frame.pack(pady=10)
    
    btn_run_test = tk.Button(test_btn_frame, text="테스트 실행", command=run_test, 
                            bg="lightblue", width=15, height=2)
    btn_run_test.pack()

    
    # 창 중앙에 배치
    test_window.update_idletasks()
    x = (test_window.winfo_screenwidth() // 2) - (500 // 2)
    y = (test_window.winfo_screenheight() // 2) - (300 // 2)
    test_window.geometry(f"500x300+{x}+{y}")

# 향후 구현 예정

def server_start():
    # VOICEVOX Engine 실행 확인 및 실행
    voice_vox_engine_path = './voicevox_engine/windows-cpu/run.exe'
    
    # VOICEVOX Engine이 실행 중인지 확인 (50021 포트 확인)
    if not is_voicevox_running():
        print('VOICEVOX Engine 시작 중...')
        if os.path.exists(voice_vox_engine_path):
            # subprocess로 백그라운드 실행
            subprocess.Popen([voice_vox_engine_path])
            # 서버 시작 대기
            if wait_for_voicevox():
                update_status("VOICEVOX Engine 구동 완료")
            else:
                update_status("VOICEVOX Engine 구동 실패")
        else:
            print(f'VOICEVOX Engine 파일을 찾을 수 없습니다: {voice_vox_engine_path}')
            update_status("VOICEVOX Engine 파일 없음")
    else:
        print('VOICEVOX Engine이 이미 실행 중입니다.')
    
    # main 서버 시작
    print('Server Start')
    update_status("Flask 서버 시작 중...")
    serve(app, host="0.0.0.0", port=5050)  # 5000 아님 주의!
    
    
if __name__ == '__main__': 
    root = tk.Tk()
    root.title("Howling")
    root.geometry("600x400")
    
    # 버튼 프레임 - 서버시작, 시작, 중지, 테스트 (grid방식)
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=0, column=0, padx=10, pady=10, columnspan=2, sticky='w')
    
    # 버튼들 생성
    btn_server_start = tk.Button(btn_frame, text="서버시작", command=start_server, width=10)
    btn_server_start.grid(row=0, column=0, padx=5, pady=5)
    
    btn_start = tk.Button(btn_frame, text="시작", command=start_listening, width=10, state='disabled')
    btn_start.grid(row=0, column=1, padx=5, pady=5)
    
    btn_stop = tk.Button(btn_frame, text="중지", command=stop_listening, width=10, state='disabled')
    btn_stop.grid(row=0, column=2, padx=5, pady=5)
    
    btn_test = tk.Button(btn_frame, text="테스트", command=test, width=10, state='disabled')
    btn_test.grid(row=0, column=3, padx=5, pady=5)
    
    # 현재 상태 - 작업중, 작업완료, 서버 시작 등의 안내문 표시
    status_frame = tk.Frame(root)
    status_frame.grid(row=1, column=0, padx=10, pady=10, columnspan=2, sticky='w')
    
    tk.Label(status_frame, text="현재 상태:").grid(row=0, column=0, sticky='w')
    status_label = tk.Label(status_frame, text="대기 중", bg="lightgray", width=50)
    status_label.grid(row=0, column=1, padx=5, sticky='w')
    
    # 전역 변수에 위젯들 할당 (전역 변수 선언 필요)
    globals()['btn_start'] = btn_start
    globals()['btn_stop'] = btn_stop  
    globals()['btn_test'] = btn_test
    globals()['status_label'] = status_label
    
    # 텍스트 프레임 - 입력된 텍스트 보여주기
    text_frame = tk.Frame(root)
    text_frame.grid(row=2, column=0, padx=10, pady=10, columnspan=2, sticky='w')
    
    tk.Label(text_frame, text="입력 텍스트:").grid(row=0, column=0, sticky='w')
    text_display = tk.Text(text_frame, height=10, width=70)
    text_display.grid(row=1, column=0, padx=5, pady=5)
    
    root.mainloop()