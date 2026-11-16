"""OMID AI - Real Security Agent (Hacking/Pentesting)"""
import os
import re
import json
import asyncio
import datetime
import subprocess
from agents.base import BaseAgent, Task, Result
from core.db import get_db

class SecurityAgent(BaseAgent):
    name = "SecurityAgent"
    display_name = "Security Expert"

    async def execute(self, task: Task) -> Result:
        self.log_event("working", {"agent": self.name, "status": "Starting security scan..."})
        
        # Extract target from task description
        target = self._extract_target(task.description)
        if not target:
            return Result(task_id=task.id, success=False, output="No valid target specified.")
            
        scan_results = {}
        report_dir = "/sdcard/omid-ai/security_scans"
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(report_dir, f"scan_{target}_{timestamp}.txt")
        
        try:
            # 1. Ping test
            self.log_event("working", {"agent": self.name, "status": f"Pinging {target}..."})
            ping_result = await self._run_command(["ping", "-c", "3", target], timeout=30)
            scan_results["ping"] = ping_result

            # 2. Nmap fast scan
            self.log_event("working", {"agent": self.name, "status": f"Running nmap on {target}..."})
            nmap_result = await self._run_command(["nmap", "-F", target], timeout=30)
            scan_results["nmap"] = nmap_result

            # 3. Whois lookup
            self.log_event("working", {"agent": self.name, "status": f"Running whois on {target}..."})
            whois_result = await self._run_command(["whois", target], timeout=30)
            scan_results["whois"] = whois_result

            # 4. Generate Persian report
            report_content = self._generate_persian_report(target, scan_results)

            # Save report to file
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            # Save to database (اصلاح شد: results باید dict باشه، نه string)
            db = get_db()
            db.save_security_scan(
                target=target,
                scan_type="ping_nmap_whois",
                results=scan_results, 
                report_path=report_path
            )

            self.log_event("complete", {
                "agent": self.name,
                "status": "Scan completed",
                "report_path": report_path,
                "results": scan_results
            })
            
            return Result(
                task_id=task.id,
                success=True,
                output={
                    "target": target,
                    "report_path": report_path,
                    "results": scan_results,
                    "persian_report": report_content
                }
            )

        except Exception as e:
            self.log_event("fail", {"agent": self.name, "status": str(e)})
            return Result(task_id=task.id, success=False, output=str(e))

    def _extract_target(self, description: str) -> str:
        """Extract IP address or domain from task description"""
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        domain_pattern = r'\b([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
        
        ip_match = re.search(ip_pattern, description)
        if ip_match:
            return ip_match.group()
            
        domain_match = re.search(domain_pattern, description)
        if domain_match:
            return domain_match.group()
            
        return None

    async def _run_command(self, cmd: list, timeout: int = 30) -> dict:
        """Run a system command with timeout and capture output"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "command": " ".join(cmd),
                    "return_code": process.returncode,
                    "stdout": stdout.decode('utf-8', errors='ignore'),
                    "stderr": stderr.decode('utf-8', errors='ignore'),
                    "success": process.returncode == 0
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "command": " ".join(cmd),
                    "error": f"Command timed out after {timeout} seconds",
                    "success": False
                }
                
        except Exception as e:
            return {
                "command": " ".join(cmd),
                "error": str(e),
                "success": False
            }

    def _generate_persian_report(self, target: str, results: dict) -> str:
        """Generate a structured Persian security report"""
        report = f"""
==================================================
OMID AI گزارش امنیتی
==================================================
==================================================

--- تست پینگ (Ping Test) ---
"""
        if "ping" in results:
            ping = results["ping"]
            if ping.get("success"):
                report += "✅ پینگ موفق بود.\n\n"
                report += ping.get("stdout", "No output")
            else:
                report += "❌ پینگ ناموفق بود.\n\n"
                report += ping.get("stderr", ping.get("error", "Unknown error"))
        else:
            report += "❌ تست پینگ اجرا نشد.\n"
            
        report += """
--------------------------------------------------
--- اسکن Nmap ---
--------------------------------------------------
"""
        if "nmap" in results:
            nmap = results["nmap"]
            if nmap.get("success"):
                report += "✅ اسکن Nmap موفق بود.\n\n"
                report += nmap.get("stdout", "No output")
            else:
                report += "❌ اسکن Nmap ناموفق بود.\n\n"
                report += nmap.get("stderr", nmap.get("error", "Unknown error"))
        else:
            report += "❌ اسکن Nmap اجرا نشد.\n"
            
        report += """
--------------------------------------------------
--- اطلاعات Whois ---
--------------------------------------------------
"""
        if "whois" in results:
            whois = results["whois"]
            if whois.get("success"):
                report += "✅ اطلاعات Whois دریافت شد.\n\n"
                report += whois.get("stdout", "No output")
            else:
                report += "❌ دریافت اطلاعات Whois ناموفق بود.\n\n"
                report += whois.get("stderr", whois.get("error", "Unknown error"))
        else:
            report += "❌ اطلاعات Whois دریافت نشد.\n"
            
        report += """
==================================================
==================================================
. پورت‌های باز شناسایی شده را بررسی و در صورت غیرضروری بودن مسدود کنید.
. برای سرویس‌های عمومی از فایروال (مانند UFW) استفاده کنید.
. نسخه سرویس‌ها را همیشه به‌روز نگه دارید.
. لاگ‌های سرور را به صورت دوره‌ای بررسی کنید.
==================================================
"""
        return report
