import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# 1. إعدادات السيطرة والمفاتيح الملكية
# ==========================================
# استبدل هذه القيم بالمفاتيح الرسمية المخصصة لنظامك
LARK_APP_ID = "ضع_هنا_APP_ID_الخاص_بـ_Logic-abdo12"
LARK_APP_SECRET = "ضع_هنا_APP_SECRET_الخاص_بـ_Logic-abdo12"
GEMINI_API_KEY = "ضع_هنا_مفتاح_API_الخاص_بمشروع_الجوزاء"

# ==========================================
# 2. بروتوكول توليد تصريح العبور (Token)
# ==========================================
def get_lark_tenant_access_token():
    """توليد رمز عبور مشفر للتحرك باسم البوت داخل Lark"""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json().get("tenant_access_token")
    except Exception as e:
        print(f"فشل في توليد تصريح العبور: {e}")
        return None

# ==========================================
# 3. توجيه الأوامر لعقل الذكاء الاصطناعي (Gemini)
# ==========================================
def ask_gemini(user_message):
    """إرسال الرسالة إلى معالج Gemini ليتخذ القرار الذكي"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": user_message}]}]
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"تأخرت استجابة المعالج المركزي: {str(e)}"

# ==========================================
# 4. معالج إرسال الرد النهائي للمجموعات
# ==========================================
def reply_to_lark_message(chat_id, text_content):
    """بث الإجابة والقرارات مباشرة داخل مجموعات العمال والموردين"""
    token = get_lark_tenant_access_token()
    if not token: 
        return
    
    url = "https://open.larksuite.com/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": "{\"text\":\"" + text_content.replace('"', '\\"') + "\"}"
    }
    requests.post(url, json=payload, headers=headers)

# ==========================================
# 5. الممر السري (Webhook) للاستماع الفوري
# ==========================================
@app.route('/webhook', methods=['POST'])
def lark_webhook():
    """المستمع الخفي لجميع الحركات والرسائل القادمة من Lark"""
    data = request.json
    
    # تأكيد أمان الرابط عند إعداده لأول مرة في Lark
    if data and "challenge" in data:
        return jsonify({"challenge": data["challenge"]}), 200
        
    # التقاط أحداث الرسائل وتمريرها للعقل المدبر
    if data and "event" in data:
        event = data["event"]
        if "message" in event:
            chat_id = event["message"].get("chat_id")
            user_text = event["message"].get("content")
            
            # منع التكرار اللانهائي (البوت لا يرد على نفسه)
            if event["sender"].get("sender_id", {}).get("open_id") != LARK_APP_ID:
                # تشغيل معالجة جيميناي
                ai_decision = ask_gemini(user_text)
                # إرجاع الرد الفوري للمجموعة
                reply_to_lark_message(chat_id, ai_decision)
                
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    # تشغيل المنظومة على المنفذ الافتراضي
    app.run(port=5000)
