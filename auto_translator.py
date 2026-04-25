# ==================================================================================
# 💡 Gemini 3.1 Flash Lite 전용 - GUI 파일 선택 창 지원 & 무한 돌파 자동 번역기
# ==================================================================================

import os
import time
import re
import ctypes
import google.generativeai as genai
from collections import deque
import tkinter as tk
from tkinter import filedialog

# --- 설정 (필수 수정) ---
GEMINI_API_KEY = '여기에_새로운_API_키를_넣으세요' 
# ------------------------

# Gemini API 설정
genai.configure(api_key="AIzaSyC8qSTVCpkFYQBV9cGHnEuartC1o77j4zo") # 사용하시는 키로 변경하세요
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

def is_traditional_chinese(text):
    """텍스트에 대만어(한자)가 포함되어 있는지 확인"""
    return any('\u4e00' <= char <= '\u9fff' for char in text)

def translate_text(text_list, chunk_size):
    """Gemini API 번역 수행"""
    if not text_list:
        return []

    prompt = (
        "Role: Professional Translator (Taiwanese Traditional Chinese to Korean).\n"
        "Task: Translate ONLY Traditional Chinese parts into natural Korean.\n"
        "Rules:\n"
        "1. Keep English, Numbers, HTML tags, JSON formatting (quotes, brackets), source code, and Symbols exactly as they are.\n"
        "2. Do NOT translate programming code, keys, or technical terms.\n"
        "3. Separate results with '|||'. No explanations."
    )
    
    try:
        response = model.generate_content(prompt + "\n\n" + "\n".join(text_list))
        
        if hasattr(response, 'text'):
            results = response.text.strip().split('|||')
            if len(results) != len(text_list):
                results = response.text.strip().split('\n')
            
            if len(results) != len(text_list):
                raise ValueError("Translation mismatch")
                
            return [t.strip() for t in results if t.strip()]
        return None
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return "QUOTA_EXCEEDED"
        
        print(f"\n   [API 통신 에러 상세 내역]: {e}")
        return None

def process_file(source_file):
    # 파일 확장자에 따라 저장할 이름 지정
    if source_file.endswith('.html'):
        target_file = source_file.replace('.html', '_kr.html')
    elif source_file.endswith('.json'):
        target_file = source_file.replace('.json', '_kr.json')
    else:
        print(f"⚠️ '{source_file}'은(는) 지원하지 않는 파일 형식입니다. 스킵합니다.")
        return True
    
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    
    start_line = 0
    if os.path.exists(target_file):
        with open(target_file, 'r', encoding='utf-8') as f:
            start_line = len(f.readlines())
            
    if start_line >= total_lines:
        print(f"✅ '{source_file}' 파일은 이미 번역이 완료되었습니다. 스킵합니다.")
        return True

    print(f"\n🎬 '{source_file}' 번역을 시작합니다. ({start_line}줄부터 이어서 시작)")

    i = start_line
    history = deque()
    processed_in_this_session = 0

    with open(target_file, 'a', encoding='utf-8') as out_f:
        while i < total_lines:
            # 다단계 청크 축소 로직 (300 -> 100 -> 50 -> 30 -> 10)
            chunk_sequence = [300, 100, 50, 30, 1]
            chunk_handled = False

            for current_chunk_size in chunk_sequence:
                chunk = lines[i:i + current_chunk_size]
                
                indices = []
                to_translate = []
                for idx, line in enumerate(chunk):
                    if source_file.endswith('.html'):
                        clean = re.sub(r'<[^>]+>', '', line).strip()
                    else:
                        clean = line.strip()

                    if clean and is_traditional_chinese(clean):
                        indices.append(idx)
                        to_translate.append(clean)

                if not to_translate:
                    out_f.writelines(chunk)
                    out_f.flush()
                    i += len(chunk)
                    processed_in_this_session += len(chunk)
                    chunk_handled = True
                    break # 현재 루프 빠져나가고 다음 i로 이동

                error_count = 0
                success_this_chunk = False
                
                while error_count < 3:
                    res = translate_text(to_translate, current_chunk_size)
                    
                    if res == "QUOTA_EXCEEDED":
                        print("\n⚠️ API 일일 사용량 또는 분당 사용량 초과 감지!")
                        print("💾 현재까지 작업한 내용은 모두 안전하게 파일에 기록되었습니다.")
                        print("🛑 프로그램을 즉시 종료합니다. 할당량이 초기화된 후 다시 실행해 주세요.")
                        return False
                    
                    if res and len(res) == len(to_translate):
                        new_chunk = list(chunk)
                        for c_idx, translated in zip(indices, res):
                            new_chunk[c_idx] = new_chunk[c_idx].replace(to_translate[indices.index(c_idx)], translated)
                        
                        out_f.writelines(new_chunk)
                        out_f.flush()
                        success_this_chunk = True
                        break # 성공했으므로 재시도 루프 탈출
                    else:
                        error_count += 1
                        if error_count < 3:
                            print(f"   ⚠️ 에러/Mismatch 발생. 5초 후 재시도... (크기: {current_chunk_size}, 실패 {error_count}/3)")
                            time.sleep(5)
                
                if success_this_chunk:
                    i += len(chunk)
                    processed_in_this_session += len(chunk)
                    chunk_handled = True
                    break # 성공했으므로 청크 축소 루프 탈출
                else:
                    if current_chunk_size > 1:
                        print(f"\n⚠️ 복잡한 문장 발견! 청크 크기를 {current_chunk_size}에서 축소하여 재시도합니다.")

            # 모든 청크(1줄짜리 포함)가 실패했을 경우 스킵 로직 작동
            if not chunk_handled:
                failed_line_number = i + 1
                print(f"\n⚠️ [번역 포기] {failed_line_number}번째 줄은 원본을 유지하고 넘어갑니다.")
                out_f.writelines([lines[i]]) # 원본 그대로 1줄 저장
                out_f.flush()
                i += 1
                processed_in_this_session += 1
            
            # 실시간 진행률 및 예상 시간 계산
            current_time = time.time()
            history.append((current_time, processed_in_this_session))
            
            while history and current_time - history[0][0] > 30:
                history.popleft()
                
            eta_min = 0
            if len(history) > 1:
                time_diff = history[-1][0] - history[0][0]
                line_diff = history[-1][1] - history[0][1]
                if time_diff > 0 and line_diff > 0:
                    speed = line_diff / time_diff
                    remaining_lines = total_lines - i
                    eta_seconds = remaining_lines / speed
                    eta_min = int(eta_seconds // 60)
            
            percentage = int((i / total_lines) * 100)
            print(f"📊 진행: {i}/{total_lines}줄 ({percentage}%) | 예상 남은 시간: {eta_min}분 (최근 30초 속도 기준)")

    print(f"\n✨ '{target_file}' 파일 번역 완료!")
    return True

def main():
    root = tk.Tk()
    root.withdraw()

    print("기다려주세요... 파일 선택 창을 엽니다.")
    file_paths = filedialog.askopenfilenames(
        title="번역할 HTML 또는 JSON 파일을 선택하세요 (다중 선택 가능)",
        filetypes=[("HTML/JSON Files", "*.html *.json"), ("All Files", "*.*")]
    )

    if not file_paths:
        print("❌ 파일 선택이 취소되었습니다. 프로그램을 종료합니다.")
        return

    target_files = [f for f in file_paths if not (f.endswith('_kr.html') or f.endswith('_kr.json'))]
    
    if not target_files:
        print("❌ 선택된 파일 중 번역할 파일이 없습니다. (이미 번역된 _kr 파일만 선택했을 수 있습니다.)")
        return

    print(f"🔍 총 {len(target_files)}개의 번역 대상 파일이 선택되었습니다.")
    
    for file in target_files:
        success = process_file(file)
        if not success:
            print("🛑 사용량 초과 또는 치명적 오류로 인해 전체 파일 처리 대기열을 중단합니다.")
            break

    try:
        ctypes.windll.user32.MessageBoxW(0, "작업이 완료되었거나 안전하게 중단되었습니다. 파일을 확인해 주세요!", "작업 알림", 0)
    except:
        pass

if __name__ == "__main__":
    main()