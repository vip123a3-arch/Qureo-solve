import asyncio
import os
import google.generativeai as genai
from flask import Flask, render_template_string, request, jsonify
from playwright.async_api import async_playwright

app = Flask(__name__)

# ================== الإعدادات ==================
GEMINI_API_KEY = "AQ.Ab8RN6KmgljTQQ1_XbDp7uZt_2clMgvScWPsJpr6r7HLLn_SOg" 
BASE_URL = "https://me-tp.qureo.education"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# ================== واجهة الموقع (HTML/CSS) ==================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة الحل الذكي | Qureo Solver</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background-color: #1e1e1e; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 90%; max-width: 400px; text-align: center; }
        h1 { color: #4CAF50; margin-bottom: 10px; font-size: 24px; }
        p { color: #bbb; margin-bottom: 20px; font-size: 14px; }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #2d2d2d; border: 1px solid #444; border-radius: 8px; color: #fff; box-sizing: border-box; font-size: 16px; }
        input:focus { border-color: #4CAF50; outline: none; }
        button { width: 100%; padding: 15px; background: linear-gradient(90deg, #4CAF50, #2E7D32); color: white; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; margin-top: 15px; transition: 0.3s; }
        button:hover { background: linear-gradient(90deg, #45a049, #1b5e20); }
        .loader { display: none; border: 4px solid #f3f3f3; border-top: 4px solid #4CAF50; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #result { margin-top: 20px; padding: 15px; border-radius: 8px; font-weight: bold; display: none; font-size: 14px; }
        .success { background: #1b5e20; color: #a5d6a7; }
        .error { background: #b71c1c; color: #ef9a9a; }
    </style>
</head>
<body>
    <div class="container">
        <h1>الحل الذكي لكوريو</h1>
        <p>أدخل بياناتك وسيقوم الذكاء الاصطناعي بحل المنصة بالكامل.</p>
        <form id="solveForm">
            <input type="text" id="student_id" placeholder="رقم الطالب (ID)" required>
            <input type="password" id="password" placeholder="كلمة المرور" required>
            <button type="submit" id="submitBtn">ابدأ الحل الآن 🚀</button>
        </form>
        <div id="loader" class="loader"></div>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('solveForm').onsubmit = async function(e) {
            e.preventDefault();
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('loader').style.display = 'block';
            document.getElementById('result').style.display = 'none';

            const studentId = document.getElementById('student_id').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch('/solve', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ student_id: studentId, password: password })
                });
                
                const data = await response.json();
                
                document.getElementById('loader').style.display = 'none';
                document.getElementById('submitBtn').disabled = false;
                
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                
                if (data.status === 'success') {
                    resultDiv.className = 'success';
                    resultDiv.innerText = data.message;
                } else {
                    resultDiv.className = 'error';
                    resultDiv.innerText = data.message;
                }
            } catch (error) {
                document.getElementById('loader').style.display = 'none';
                document.getElementById('submitBtn').disabled = false;
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.className = 'error';
                resultDiv.innerText = "حدث خطأ في الاتصال بالسيرفر.";
            }
        };
    </script>
</body>
</html>
"""

# ================== الذكاء الاصطناعي ==================
async def ask_gemini_to_solve(question_text):
    try:
        prompt = f"أنت خبير برمجة. اكتب الكود المطلوب فقط لحل هذا السؤال، بدون أي كلام إضافي أو تنسيقات مارك داون (بدون ```):\n{question_text}"
        response = model.generate_content(prompt)
        answer = response.text.strip()
        return answer.replace("```javascript", "").replace("```", "").strip()
    except Exception:
        return None

# ================== المتصفح المخفي (Playwright) ==================
async def solve_qureo(student_id, password):
    async with async_playwright() as p:
        # استخدام المتصفح المخفي
        browser = await p.chromium.launch(headless=True) 
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. الدخول
            await page.goto(f"{BASE_URL}/login")
            await page.fill('input[type="text"]', student_id)
            await page.fill('input[type="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(5000)
            
            if "login" in page.url:
                await browser.close()
                return {"status": "error", "message": "فشل تسجيل الدخول. تأكد من البيانات."}
            
            # 2. التوجه للفصل الأول
            await page.goto(f"{BASE_URL}/chapter/1")
            await page.wait_for_timeout(4000)
            
            solved = 0
            # 3. اللف على الأسئلة
            while True:
                try:
                    question_element = await page.wait_for_selector('.question-text', timeout=3000)
                    if not question_element:
                        break
                    
                    question_text = await question_element.inner_text()
                    
                    editor = await page.query_selector('.code-editor-class')
                    if editor:
                        code = await ask_gemini_to_solve(question_text)
                        if code:
                            await editor.fill(code)
                            run_btn = await page.query_selector('button:has-text("تشغيل الكود")')
                            if run_btn: await run_btn.click()
                            await page.wait_for_timeout(2000)
                            confirm_btn = await page.query_selector('button:has-text("تأكيد")')
                            if confirm_btn: await confirm_btn.click()
                            await page.wait_for_timeout(1000)
                            solved += 1
                except Exception:
                    break
            
            await browser.close()
            return {"status": "success", "message": f"تم حل {solved} سؤال بنجاح في هذا الفصل!"}
            
        except Exception as e:
            await browser.close()
            return {"status": "error", "message": f"حدث خطأ: {str(e)}"}

# ================== الراوتس (Routes) ==================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json
    student_id = data.get('student_id')
    password = data.get('password')
    
    if not student_id or not password:
        return jsonify({"status": "error", "message": "يرجى إدخال البيانات كاملة."})
    
    # تشغيل السكريبت
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(solve_qureo(student_id, password))
    
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
