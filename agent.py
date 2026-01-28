import os
import json
import subprocess
from pathlib import Path
import ollama

# Configurações
MODEL = "phi3"
WORKSPACE = Path.home() / "IA-Agent"
WORKSPACE.mkdir(exist_ok=True)
SESSION_FILE = WORKSPACE / "session.json"

def load_session():
    if SESSION_FILE.exists():
        return json.loads(SESSION_FILE.read_text())
    return {"history": []}

def save_session(data):
    SESSION_FILE.write_text(json.dumps(data, indent=2))

def ask_llm(prompt, context=""):
    full_prompt = f"""Você é um assistente técnico chamado AgentLocal. 
Trabalhe apenas dentro da pasta {WORKSPACE}. 
Nunca execute comandos perigosos. Sempre responda em JSON com:
{{"action": "read_file|write_file|run_command|respond", "path": "...", "content": "...", "command": "...", "message": "..."}}

Contexto anterior: {context}
Tarefa do usuário: {prompt}"""
    
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": full_prompt}])
    return response['message']['content']

def safe_run_command(cmd):
    blocked = ["rm -rf", "sudo", "dd", "mkfs", ":(){ :|:& };:", "format", "del /s", "rd /s"]
    if any(b in cmd for b in blocked):
        return "Comando bloqueado por segurança."
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=WORKSPACE, 
            capture_output=True, 
            text=True, 
            timeout=20,
            env={**os.environ, 'HOME': str(Path.home())}
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"Erro: {e}"

def process_action(action_json_str):
    try:
        action = json.loads(action_json_str)
        atype = action.get("action")
        
        if atype == "read_file":
            path = WORKSPACE / action["path"]
            return path.read_text() if path.exists() else "Arquivo não encontrado."
        
        elif atype == "write_file":
            path = WORKSPACE / action["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(action["content"], encoding='utf-8')
            return f"Arquivo salvo: {path}"
        
        elif atype == "run_command":
            return safe_run_command(action["command"])
        
        elif atype == "respond":
            return action.get("message", "")
        
        else:
            return "Ação desconhecida."
    except Exception as e:
        return f"Erro ao processar ação: {e}"

if __name__ == "__main__":
    session = load_session()
    print(f"📁 Trabalhando em: {WORKSPACE}")
    print("Digite 'sair' para encerrar.\n")

    while True:
        user_input = input("Você: ")
        if user_input.lower() == "sair":
            break

        context = "\n".join([f"- {h}" for h in session["history"][-3:]])
        raw_response = ask_llm(user_input, context)
        print(f"\n🧠 Agente pensou: {raw_response[:200]}...")

        output = process_action(raw_response)
        print(f"✅ Resultado: {output}\n")

        session["history"].append(f"Usuário: {user_input}")
        session["history"].append(f"Agente: {output}")
        save_session(session)