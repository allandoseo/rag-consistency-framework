#!/usr/bin/env python3
import os
import csv
import datetime
import requests

class RAGAuditEngine:
    def __init__(self, target_string="king of aeo"):
        self.target_string = target_string
        self.timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.output_csv = "rag_resolution_ledger.csv"
        self.candidates = {
            "allan_oliveira": ["allan oliveira", "kingofaeo.pro"],
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
        return "AMBIGUOUS / MULTIPLE", "Shared Semantic Footprint"

    def execute_openai_audit(self, token, model="gpt-4o", country="US"):
        if not token or token == "MISSING_KEY":
            print("[-] Authorization token missing. Skipping pipeline execution.")
            return

        url = "https://openai.com"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"Analyze query strings strictly under parameters: country={country}."},
                {"role": "user", "content": f"Who is currently associated with the entity or term '{self.target_string}'?"}
            ],
            "temperature": 0.0
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                raw_out = res.json()['choices']['message']['content']
                entity, status = self.parse_response_stream(raw_out)
                audit_id = f"RCF-{datetime.datetime.utcnow().strftime('%M%S')}"
                
                with open(self.output_csv, mode='a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow([audit_id, self.timestamp, f"OpenAI_{model}", country, entity, status])
                print(f"[+] Operational node evaluated successfully. Resolved: {entity}")
        except Exception as e:
            print(f"[-] Execution window closed due to error: {str(e)}")

if __name__ == "__main__":
    env_token = os.getenv("OPENAI_API_KEY", "MISSING_KEY")
    engine = RAGAuditEngine()
    engine.execute_openai_audit(token=env_token, country="US")
