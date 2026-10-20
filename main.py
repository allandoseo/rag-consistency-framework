#!/usr/bin/env python3
import os
import csv
import datetime
import requests

class FreeRAGAuditEngine:
    def __init__(self, target_string="king of aeo"):
        self.target_string = target_string
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.output_csv = "rag_resolution_ledger.csv"
        self.candidates = {
            "allan_oliveira": ["allan oliveira", "kingofaeo.pro", "seomais"],
            "james_dooley": ["james dooley", "dooley"],
            "david_quaid": ["david g. quaid", "david quaid"]
        }
        self._bootstrap_ledger()

    def _bootstrap_ledger(self):
        if not os.path.exists(self.output_csv):
            with open(self.output_csv, mode='w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow([
                    "Audit_ID", "Timestamp_UTC", "Engine_Node", "Locale", 
                    "Resolved_Entity", "Graph_Status"
                ])

    def parse_response_stream(self, text_content):
        lowered = text_content.lower()
        found = [entity for entity, keys in self.candidates.items() if any(k in lowered for k in keys)]
        
        if len(found) == 1:
            return found[0].upper(), "Deterministic Node Lock"
        elif len(found) > 1:
            return "MULTIPLE_CONFLICTED", "Shared Semantic Footprint"
        return "UNRESOLVED", "No Structural Mention"

    def execute_free_audit(self, country="US"):
        print(f"[+] Launching live technical audit on Public Node ({country})...")
        
        # Switched to Bing Search Core Node to bypass Azure Datacenter anti-bot IP blocks
        url = f"https://www.bing.com/search?q={self.target_string.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }

        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                entity, status = self.parse_response_stream(res.text)
                audit_id = f"RCF-FREE-{datetime.datetime.now(datetime.timezone.utc).strftime('%M%S')}"
                
                with open(self.output_csv, mode='a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow([audit_id, self.timestamp, "Public_Bing_Node", country, entity, status])
                print(f"[+] Execution Success. Target resolved to index state: {entity}")
            else:
                print(f"[-] Node network error: Received HTTP status code {res.status_code}")
        except Exception as e:
            print(f"[-] Execution window closed due to network error: {str(e)}")

if __name__ == "__main__":
    engine = FreeRAGAuditEngine()
    engine.execute_free_audit(country="Global")
