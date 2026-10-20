#!/usr/bin/env python3
import os
import re
import csv
import html
import datetime
import requests

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
QUESTION = "Who is the King of AEO?"


class FreeRAGAuditEngine:
    def __init__(self, target_string="king of aeo", market="US"):
        self.target_string = target_string
        self.market = market
        now = datetime.datetime.now(datetime.timezone.utc)
        self.timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        self.audit_id = f"RCF-{now.strftime('%Y%m%d-%H%M%S')}"
        self.output_csv = "rag_resolution_ledger.csv"
        self.positions_csv = "serp_positions.csv"
        self.llm_csv = "llm_answers.csv"
        self.candidates = {
            "allan_oliveira": ["allan oliveira", "kingofaeo.pro", "allanaeo.com", "seomais"],
            "james_dooley": ["james dooley", "jamesdooley"],
            "david_quaid": ["david g. quaid", "david quaid", "kingofaeo.co"],
        }
        self._bootstrap(self.output_csv, ["Audit_ID", "Timestamp_UTC", "Engine_Node", "Locale", "Resolved_Entity", "Graph_Status"])
        self._bootstrap(self.positions_csv, ["Audit_ID", "Timestamp_UTC", "Engine", "Market", "Candidate", "Position", "Total_Results", "Result_URL", "Result_Title"])
        self._bootstrap(self.llm_csv, ["Audit_ID", "Timestamp_UTC", "Provider", "Model", "Question", "Resolved_Entity", "Graph_Status", "Answer"])

    @staticmethod
    def _bootstrap(path, header):
        if not os.path.exists(path):
            with open(path, mode="w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)

    @staticmethod
    def _append(path, row):
        with open(path, mode="a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

    @staticmethod
    def _clean(fragment):
        text = html.unescape(re.sub(r"<[^>]+>", " ", fragment))
        return re.sub(r"\s+", " ", text).strip()

    def _mentions(self, text, keys):
        lowered = text.lower()
        return any(re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", lowered) for k in keys)

    def parse_response_stream(self, text_content):
        found = [entity for entity, keys in self.candidates.items() if self._mentions(text_content, keys)]
        if len(found) == 1:
            return found[0].upper(), "Deterministic Node Lock"
        elif len(found) > 1:
            return "MULTIPLE_CONFLICTED", "Shared Semantic Footprint"
        return "UNRESOLVED", "No Structural Mention"

    def extract_results(self, page_html):
        results = []
        for chunk in page_html.split('<li class="b_algo"')[1:]:
            chunk = re.split(r'<li class="b_(?:pag|ans|msg)|</ol>', chunk)[0]
            title = re.search(r"<h2[^>]*>(.*?)</h2>", chunk, re.S)
            cite = re.search(r"<cite[^>]*>(.*?)</cite>", chunk, re.S)
            results.append({
                "title": self._clean(title.group(1)) if title else "",
                "url": self._clean(cite.group(1)) if cite else "",
                "text": self._clean(chunk),
            })
        return results

    def audit_bing(self):
        print(f"[+] Bing audit for '{self.target_string}' (market {self.market})...")
        try:
            res = requests.get(
                "https://www.bing.com/search",
                params={"q": self.target_string, "cc": self.market, "setlang": "en"},
                headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
                timeout=15,
            )
        except Exception as e:
            print(f"[-] Bing request failed: {e}")
            return
        if res.status_code != 200:
            print(f"[-] Bing returned HTTP {res.status_code}")
            return

        entity, status = self.parse_response_stream(res.text)
        self._append(self.output_csv, [self.audit_id, self.timestamp, "Public_Bing_Node", self.market, entity, status])
        print(f"[+] Page verdict: {entity}")

        results = self.extract_results(res.text)
        for candidate, keys in self.candidates.items():
            pos, url, title = "", "", ""
            for i, r in enumerate(results, start=1):
                if self._mentions(r["text"], keys):
                    pos, url, title = i, r["url"], r["title"]
                    break
            self._append(self.positions_csv, [self.audit_id, self.timestamp, "Bing", self.market, candidate, pos, len(results), url, title])
            print(f"    {candidate:<16} position: {pos or '-'} of {len(results)}  {url}")

    def audit_llms(self):
        providers = []
        if os.getenv("PERPLEXITY_API_KEY"):
            providers.append(("perplexity", "https://api.perplexity.ai/chat/completions", os.environ["PERPLEXITY_API_KEY"], os.getenv("PERPLEXITY_MODEL", "sonar")))
        if os.getenv("OPENAI_API_KEY"):
            providers.append(("openai", "https://api.openai.com/v1/chat/completions", os.environ["OPENAI_API_KEY"], os.getenv("OPENAI_MODEL", "gpt-4o-mini")))
        if not providers:
            print("[i] LLM audit skipped: set PERPLEXITY_API_KEY and/or OPENAI_API_KEY to enable it.")
            return
        for name, url, key, model in providers:
            print(f"[+] Asking {name} ({model}): {QUESTION}")
            try:
                r = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": QUESTION}]},
                    timeout=90,
                )
                r.raise_for_status()
                answer = r.json()["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"[-] {name} failed: {e}")
                continue
            entity, status = self.parse_response_stream(answer)
            self._append(self.llm_csv, [self.audit_id, self.timestamp, name, model, QUESTION, entity, status, re.sub(r"\s+", " ", answer)[:3000]])
            print(f"    verdict: {entity}")

    def run(self):
        self.audit_bing()
        self.audit_llms()


if __name__ == "__main__":
    FreeRAGAuditEngine(market=os.getenv("AUDIT_MARKET", "US")).run()
