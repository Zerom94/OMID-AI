import subprocess
import asyncio

def _run_git_commands(message: str) -> str:
    try:
        # ۱. تنظیم موقت SSL برای اندروید
        subprocess.run(["git", "config", "--global", "http.sslVerify", "false"], cwd="/sdcard/omid-ai", check=True)
        
        # ۲. افزودن و کامیت کردن
        subprocess.run(["git", "add", "."], cwd="/sdcard/omid-ai", check=True)
        subprocess.run(["git", "commit", "-m", message], cwd="/sdcard/omid-ai", check=True, capture_output=True)
        
        # ۳. پوش به گیت‌هاب (با --force برای جلوگیری از تداخل)
        result = subprocess.run(["git", "push", "origin", "main", "--force"], cwd="/sdcard/omid-ai", check=True, capture_output=True, text=True)
        
        # ۴. برگرداندن SSL به حالت امن
        subprocess.run(["git", "config", "--global", "http.sslVerify", "true"], cwd="/sdcard/omid-ai", check=True)
        
        return "✅ کدها با موفقیت به گیت‌هاب پوش شدند."
    except subprocess.CalledProcessError as e:
        subprocess.run(["git", "config", "--global", "http.sslVerify", "true"], cwd="/sdcard/omid-ai")
        error_msg = e.stderr if e.stderr else str(e)
        return f"❌ خطا در عملیات گیت: {error_msg}"

async def push_to_github(message: str) -> str:
    return await asyncio.to_thread(_run_git_commands, message)
