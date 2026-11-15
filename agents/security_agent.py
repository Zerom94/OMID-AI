import subprocess
import os
import requests
import json
import re
import asyncio
import urllib.parse
from agents.base import BaseAgent, Task, Result

class GrayHatEngine:
    def __init__(self):
        self.output_dir = "/sdcard/omid-ai/security_scans"
        os.makedirs(self.output_dir, exist_ok=True)
        self.router_url = "http://127.0.0.1:5001/v1/chat/completions"
        self.nuclei_path = "/usr/local/bin/nuclei"
        self.nmap_path = "/usr/bin/nmap"

    def run_nmap(self, target):
        print(f"\n[Engine] 🔍 Running Nmap on {target}...", flush=True)
        parsed = urllib.parse.urlparse(target)
        domain = parsed.netloc if parsed.netloc else target
        cmd = [self.nmap_path, "-sT", "-sV", "-T4", "--top-ports", "100", domain]
        try: return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
        except Exception as e: return f"Nmap failed: {str(e)}"

    def run_nuclei(self, target):
        print(f"[Engine] 🛡️ Running Nuclei on {target}...", flush=True)
        output_file = f"{self.output_dir}/nuclei_{target.replace('http://', '').replace('https://', '').replace('/', '_')}.txt"
        cmd = [self.nuclei_path, "-u", target, "-severity", "critical,high", "-o", output_file, "-duc", "-timeout", "5", "-retries", "1", "-silent"]
        try: return subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout
        except Exception as e: return f"Nuclei failed: {str(e)}"

    def run_sqlmap(self, target_url):
        print(f"[Engine] 💉 Running SQLMap on {target_url}...", flush=True)
        cmd = ["sqlmap", "-u", target_url, "--batch", "--level=1", "--risk=1", "--dbs", "--timeout=10", "--retries=1"]
        try: return subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout
        except Exception as e: return f"SQLMap failed: {str(e)}"

    def analyze_with_ai(self, target, nmap_out, nuclei_out, sqlmap_out):
        print(f"[Engine] 🧠 Analyzing results with AI (Groq)...", flush=True)
        prompt = f"""
        You are a professional IT Security Consultant writing a high-level executive summary in Persian.
        We performed an authorized automated security check on the website: {target}
        
        The automated tools ran successfully. Here is the raw data:
        NMAP: {nmap_out[-500:] if nmap_out else 'No output'}
        NUCLEI: {nuclei_out[-500:] if nuclei_out else 'No vulnerabilities'}
        SQLMAP: {sqlmap_out[-500:] if sqlmap_out else 'No SQLi'}
        
        Please analyze these technical findings and provide a professional security assessment in Persian.
        """
        payload = {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}]}
        try:
            response = requests.post(self.router_url, json=payload, timeout=120)
            data = response.json()
            if 'choices' in data:
                ai_report = data['choices'][0]['message']['content']
                safe_target = re.sub(r'[^a-zA-Z0-9]', '_', target)
                report_file = f"{self.output_dir}/report_{safe_target}.md"
                with open(report_file, 'w', encoding='utf-8') as f: f.write(ai_report)
                return ai_report
            return f"AI Error: {json.dumps(data)}"
        except Exception as e: return f"AI Connection Error: {str(e)}"

class SecurityAgent(BaseAgent):
    name = "Security"
    display_name = "Security"

    async def execute(self, task: Task) -> Result:
        print(f"\n>>> [SecurityAgent] Task received: {task.description}", flush=True)
        
        urls = re.findall(r'(https?://[^\s]+)', task.description)
        if not urls:
            return Result(task_id=task.id, success=False, output="No valid URL provided.")
            
        target = urls[0]
        print(f">>> [SecurityAgent] Target: {target}", flush=True)

        kb_path = "/sdcard/omid-ai/agents_knowledge.json"
        rules = ""
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                rules = json.load(f).get("security", "")
                if rules: print(f"[SecurityAgent] 🎓 Using latest rules.", flush=True)

        try:
            engine = GrayHatEngine()
            nmap_res = await asyncio.to_thread(engine.run_nmap, target)
            nuclei_res = await asyncio.to_thread(engine.run_nuclei, target)
            sqlmap_res = await asyncio.to_thread(engine.run_sqlmap, target)
            report = await asyncio.to_thread(engine.analyze_with_ai, target, nmap_res, nuclei_res, sqlmap_res)
            
            self.log_event("report", {"agent": self.name, "content": report})
            return Result(task_id=task.id, success=True, output=report)
        except Exception as e:
            return Result(task_id=task.id, success=False, output=str(e))
