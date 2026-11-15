import subprocess
import asyncio

def _run_git_commands(message: str) -> str:
    try:
        # ۱. تنظیم موقت SSL برای اندروید
        subprocess.run(["git", "config", "--global", "http.sslVerify", "false"], cwd="/sdcard/omid-ai", check=True)
        
        # ۲. افزودن و کامیت کردن
        subprocess.run(["git", "add", "."], cwd="/sdcard/omid-ai", check=True)
        subprocess.run(["git", "commit", "-m", message], cwd="/sdcard/omid-ai", check=True, capture_output=True)
        
        # ۳. پوش به گیت‌هاب
        result = subprocess.run(["git", "push", "origin", "main"], cwd="/sdcard/omid-ai", check=True, capture_output=True, text=True)
        
        # ۴. برگرداندن SSL به حالت امن
        subprocess.run(["git", "config", "--global", "http.sslVerify", "true"], cwd="/sdcard/omid-ai", check=True)
        
        return "✅ کدها با موفقیت به گیت‌هاب پوش شدند."
    except subprocess.CalledProcessError as e:
        # در صورت بروز خطا، SSL را به حالت امن برمی‌گردانیم
        subprocess.run(["git", "config", "--global", "http.sslVerify", "true"], cwd="/sdcard/omid-ai")
        error_msg = e.stderr if e.stderr else str(e)
        return f"❌ خطا در عملیات گیت: {error_msg}"

async def push_to_github(message: str) -> str:
    # اجرای دستورات گیت در یک Thread جداگانه تا سیستم هنگ نکند
    return await asyncio.to_thread(_run_git_commands, message)
