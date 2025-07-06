import re
import tkinter as tk

# Server-Flask
from flask import Flask, Response, request, jsonify, send_file, abort
from waitress import serve

# Local
import util_voicevox

app = Flask(__name__)

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
        result = util_voicevox.voicevox_tts(text)  # 'output*.wav'
        response = send_file(result, mimetype="audio/wav")
        return response
    except:
        pass
    
    # return 되지 않았다면 언어필요없이 gtts로 반환
    
def server_start():
    # subprocess로 run.exe 실행
    voice_vox_engine_path = './voicevox_engine/windows-cpu/run.exe'
    
    # main 서버 시작
    print('Server Start')
    serve(app, host="0.0.0.0", port=5050)  # 5000 아님 주의!
    
    
if __name__ == '__main__': 
    root = tk.Tk()
    root.title("Howling")
    # 크기 변경 geometry
    
    # 버튼 프레임 - 서버시작, 시작, 중지, 테스트 (grid방식)
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=0, column=0, padx=10, pady=10, columnspan=2, sticky='w')
    
    # 텍스트 프레임 - 입력된 텍스트 보여주기
    
    # 현재 상태 - 작업중, 작업완료, 서버 시작 등의 안내문 표시
    

    
    root.mainloop()