import google.generativeai as genai
import os

try:
    # 強烈建議使用環境變數儲存 API KEY (如先前所述)
    GEMINI_API_KEY = 'AIzaSyChx2x9fVh-ZTFvULaUJh5stYGa2W9FzkI' # 請替換成你有效的金鑰

    if not GEMINI_API_KEY:
        print("錯誤：GEMINI_API_KEY 未設定。")
    else:
        genai.configure(api_key=GEMINI_API_KEY)

        print("正在列出可用的模型...")
        for m in genai.list_models():
            # 檢查模型是否支援 'generateContent' 方法
            if 'generateContent' in m.supported_generation_methods:
                print(f"模型名稱: {m.name}, 支援 generateContent")
                # 你也可以印出其他資訊:
                # print(f"  顯示名稱: {m.display_name}")
                # print(f"  描述: {m.description}")
                # print(f"  支援的方法: {m.supported_generation_methods}\n")


        # 在確認模型名稱後，你可以嘗試再次生成內容
        # 假設 'gemini-1.0-pro' 或 'gemini-pro' 在列表中且支援 generateContent
        print("\n嘗試使用 'gemini-1.0-pro' (如果可用) 或 'gemini-pro' 生成內容...")
        # 你可能需要根據上面列出的模型名稱調整
        # 常見的可能是 'gemini-pro' 或 'gemini-1.0-pro'
        # 或是選擇一個確定支援 'generateContent' 的模型
        model_to_use = 'gemma-3-1b-it' # 或者 'gemini-pro'，或從上面列表選一個
        try:
            print(f"嘗試使用模型: {model_to_use}")
            model_instance = genai.GenerativeModel(model_to_use)
            prompt = "你好嗎？"
            print(f"正在向 Gemini ({model_to_use}) 發送請求: '{prompt}'")
            response = model_instance.generate_content(prompt)
            print(f"Gemini ({model_to_use}) 回應:", response.text)
        except Exception as e_gen:
            print(f"使用模型 {model_to_use} 生成內容時發生錯誤: {e_gen}")


except Exception as e:
    print(f"獨立測試 Gemini 時發生錯誤: {e}")
    import traceback
    traceback.print_exc()