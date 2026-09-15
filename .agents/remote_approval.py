import sys
import json
import time
import os
import uuid
import requests
import tempfile

TEMP_DIR = tempfile.gettempdir()
TOKEN = "8980284332:AAEo8LPw92CvcbbT4ut6yhoqNwgWlqLzBGU"
CHAT_ID = "5463025868"

def main():
    try:
        input_data = sys.stdin.read()
        payload = json.loads(input_data)
        
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        
        safe_tools = ["view_file", "search_web", "list_dir", "grep_search", "find_by_name", "read_url_content", "manage_task", "send_message", "schedule", "ask_question"]
        if tool_name in safe_tools:
            print(json.dumps({"decision": "allow"}))
            return
            
        req_id = str(uuid.uuid4())[:8]
        
        args_str = json.dumps(tool_call.get("args", {}), indent=2)
        text = f"⚠️ *Approval Required*\nLnThe agent wants to perform:\n\n*Tool*:\n`{tool_name}`\n\n*Arguments*:\n```json\n{args_str}\n```"
        
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✉ Allow", "callback_data": f"approve_{req_id}"},
                    {"text": "♂ Deny", "callback_data": f"deny_{req_id}"}
                ]
            ]
        }
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup
        })
        
        if resp.status_code != 200:
            print(json.dumps({"decision": "ask", "reason": f"Failed to send Telegram approval request: {resp.text}"}))
            return
            
        message_id = resp.json().get("result", {}).get("message_id")
            
        result_file = os.path.join(TEMP_DIR, f"approval_{req_id}.result")
        
        timeout = 300 
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if os.path.exists(result_file):
                with open(result_file, "r") as f:
                    decision = f.read().strip()
                os.remove(result_file)
                if decision == "approve": decision = "allow"
                print(json.dumps({"decision": decision}))
                return
            time.sleep(1)
            
        edit_url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
        requests.post(edit_url, json={
            "chat_id": CHAT_ID,
            "message_id": message_id,
            "text": text + "\n\n[ ❍ Timed out ]",
            "parse_mode": "Markdown"
        })
        print(json.dumps({"decision": "deny", "reason": "Remote approval timed out."}))
        
    except Exception as e:
        print(json.dumps({"decision": "ask", "reason": f"Remote approval hook crashed: {str(e)}"}))

if __name__ == "__main__":
    main()

