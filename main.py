# main.py - AI Agent dengan 3 Custom Tools (File Organizer, System Check, Database Query)

import requests, json
import pandas as pd # Dipertahankan untuk kompatibilitas
import os, shutil
from colorama import Fore, Style, init
import psutil # Digunakan untuk System Check

# Inisialisasi colorama (agar warna berfungsi di berbagai terminal)
init(autoreset=True)

# --- 1. Konfigurasi API dan Warna Terminal ---

# GANTI DENGAN KUNCI OPENROUTER API ANDA YANG SEBENARNYA!
a = "sk-or-v1-7995770d42"
b = "78c5cbb2d0ab4335adf3"
c = "b69dfff451870ce8"
d = "9f73cf8b7a9544ce02"

OPENROUTER_API_KEY = a + b + c + d
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "x-ai/grok-4-fast"

# Warna Sesuai Tugas (Hijau untuk User, Cyan untuk Output Agent)
COLOR_USER = Fore.GREEN
COLOR_AGENT = Fore.CYAN
COLOR_THINKING = Fore.YELLOW
COLOR_TOOL = Fore.BLUE

# --- 2. Custom Tools Unik (3 Tools) ---

# A. Tool 1: File Organizer (SUDAH DIMODIFIKASI UNTUK NAMA FOLDER EKSTENSI)
def smart_file_organizer(path: str, extension: str) -> str:
    """
    Scans a directory for files of a specific extension and moves them 
    to a new subfolder named after the extension (e.g., 'PDF' or 'JPG').
    """
    if not os.path.isdir(path):
        return f"Error: Directory path '{path}' not found or is invalid."

    # 1. Tentukan nama subfolder baru berdasarkan ekstensi (dibuat Kapital)
    subfolder_name = extension.upper().replace('.', '') 
    # 2. Definisikan jalur folder baru
    organized_dir = os.path.join(path, subfolder_name)
    
    # 3. Buat folder baru jika belum ada
    if not os.path.exists(organized_dir):
        os.makedirs(organized_dir)

    moved_count = 0
    
    # Pastikan ekstensi diawali titik jika belum ada
    if not extension.startswith('.'):
        extension_filter = '.' + extension.lower()
    else:
        extension_filter = extension.lower()

    # Memindai dan memindahkan file
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path) and item.lower().endswith(extension_filter):
            try:
                shutil.move(item_path, os.path.join(organized_dir, item))
                moved_count += 1
            except Exception as e:
                return f"Error moving file {item}: {e}"

    # Hasil Akhir Tool
    if moved_count > 0:
        # Pesan sukses diubah untuk mencantumkan nama subfolder
        return f"Berhasil memindahkan {moved_count} file {extension.upper()} ke subfolder '{subfolder_name}' di '{path}'."
    else:
        return f"Tidak ditemukan file dengan ekstensi {extension.upper()} di direktori '{path}'."


# B. Tool 2: System Check
def system_check() -> str:
    """
    Checks and returns current system status, including CPU usage and available RAM.
    """
    cpu_usage = psutil.cpu_percent(interval=1)
    
    mem = psutil.virtual_memory()
    total_gb = round(mem.total / (1024**3), 2)
    available_gb = round(mem.available / (1024**3), 2)
    used_percent = mem.percent
    
    result = (f"System Status:\n"
              f"- CPU Usage: {cpu_usage}%\n"
              f"- RAM Total: {total_gb} GB\n"
              f"- RAM Available: {available_gb} GB\n"
              f"- RAM Used: {used_percent}%")
    return result


# C. Tool 3: Database Query (Simulasi)
def database_query(user_id: str) -> str:
    """
    Simulates querying a user profile from a database using a User ID.
    Returns the user data if found.
    """
    
    # --- SIMULASI DATA PENGGUNA ---
    database = {
        "USR100": {"name": "Budi Santoso", "status": "Active", "last_login": "2025-11-20", "role": "Developer"},
        "USR205": {"name": "Sinta Dewi", "status": "Suspended", "last_login": "2025-10-01", "role": "Admin"},
        "USR330": {"name": "Joko Susilo", "status": "Active", "last_login": "2025-11-21", "role": "Tester"},
    }
    # ---------------------
    
    data = database.get(user_id.upper())
    
    if data:
        return f"Data ditemukan untuk User ID {user_id.upper()}: {json.dumps(data)}"
    else:
        return f"Error: User ID {user_id.upper()} tidak ditemukan dalam database."


# Dictionary untuk memetakan nama tool ke fungsi Python
tool_dictionary = {
    "smart_file_organizer": smart_file_organizer,
    "system_check": system_check,
    "database_query": database_query,
}

# Skema JSON yang memberitahu LLM cara memanggil tools ini
tool_schema = [
    {
        "type": "function",
        "function": {
            "name": "smart_file_organizer",
            "description": "Organizes files in a specified directory. Scans a folder for files of a specific type (extension) and moves them into a new subfolder named after the extension (e.g., 'PDF' or 'JPG').",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The target directory path (e.g., 'C:/Users/User/Downloads')."},
                    "extension": {"type": "string", "description": "The file extension to filter and organize (e.g., 'pdf', 'jpg', 'py')."}
                },
                "required": ["path", "extension"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "system_check",
            "description": "Checks the current computer's performance, including CPU usage and available RAM. Use this for requests asking about system status or memory.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "database_query",
            "description": "Searches for and returns a user's profile data from a simulated database using a unique User ID (e.g., USR100, USR205).",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The unique ID of the user to search for (e.g., 'USR100', 'USR205')."}
                },
                "required": ["user_id"]
            }
        }
    }
]


# --- 3. Kelas LLM_API_AGENT (Dengan Tool-Calling Logic) ---

class LLM_API_AGENT:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        self.payload = {"model": MODEL_NAME, "messages": [], "tools": tool_schema, "tool_choice": "auto", "stream": True}
    
    def set_system_prompt(self, system_prompt: str):
        self.payload['messages'].append({"role": "system", "content": system_prompt})
    
    def add_message(self, role: str, content: str):
        self.payload['messages'].append({"role": role, "content": content})
    
    def add_tool_call(self, tool_call_id: str, tool_call_response: str):
        self.payload['messages'].append({
            "role": "tool",
            "content": tool_call_response,
            "tool_call_id": tool_call_id
        })
    
    def get_response(self):
        response = requests.post(f"{OPENROUTER_BASE_URL}/chat/completions", headers=self.headers, json=self.payload, stream=True)
        tool_calls = []
        response.raise_for_status()
        
        response_text = ""
        for chunk in response.iter_lines():
            if chunk:
                data = chunk.decode('utf-8')    
                if data.startswith('data: '):
                    data = data[6:]
                    if data.strip() != '[DONE]':
                        try:
                            data = json.loads(data)
                            delta = data['choices'][0]['delta']
                            
                            content_chunk = delta.get('content')
                            if content_chunk:
                                print(f"{COLOR_AGENT}{content_chunk}", end='', flush=True) 
                                response_text += content_chunk
                                
                            if delta.get('tool_calls'):
                                for tool in delta['tool_calls']:
                                    if tool['function'].get('arguments'):
                                        arg = json.loads(tool['function']['arguments'])
                                        tool_calls.append({
                                            "tool_call_id": tool['id'],
                                            "name": tool['function']['name'],
                                            "arguments": arg
                                        })
                        except json.JSONDecodeError:
                            continue

        return response_text, tool_calls


# --- 4. Main Agent Loop Interaktif (CLI Interface) ---

# Inisialisasi Agent
agent = LLM_API_AGENT()
# UPDATE SYSTEM PROMPT: memberitahu LLM bahwa ia memiliki 3 tools
agent.set_system_prompt("You are a helpful and versatile System Administrator Assistant. You have access to three custom tools: 'smart_file_organizer' for file management, 'system_check' for monitoring computer performance, and 'database_query' for finding user data. Analyze the user's request and choose the appropriate tool.")

print(f"{COLOR_AGENT}=== AI Admin Agent Terminal Interface ({len(tool_dictionary)} Tools Aktif) ==={Style.RESET_ALL}")
print(f"{COLOR_AGENT}HALO ABDUL")
print("-" * 50) # Garis pemisah baru
print(f"{COLOR_AGENT}Instruksi Uji Coba:")
print(f"{COLOR_AGENT}1. System Check: 'cek sisa RAM di laptop saya'")
print(f"{COLOR_AGENT}2. File Organizer: 'rapikan file PDF di D:/ai_agent_project/UJI_COBA_AGENT'")
print(f"{COLOR_AGENT}3. Database Query: 'cari data untuk user USR100'")
print("-" * 50) # Garis pemisah baru
print(f"{COLOR_AGENT}Ketik 'q' untuk keluar.")
print("=" * 50)


while True:
    try:
        user_input = input(f"{COLOR_USER}You: {Style.RESET_ALL}") 
        
        if user_input.lower() in ['q', 'quit', 'exit']:
            print(f"{COLOR_AGENT}Goodbye!")
            break
        
        agent.add_message("user", user_input)
        
        print(f"{COLOR_THINKING}[AI Thinking]: Memproses permintaan...{Style.RESET_ALL}")
        
        while True:
            response, tool_calls = agent.get_response()
            
            if len(tool_calls) > 0:
                tool = tool_calls[0]
                tool_name = tool['name']
                tool_args = tool['arguments']
                tool_call_id = tool['tool_call_id']

                print(f"\n{COLOR_TOOL}[Tool Call]: Memanggil {tool_name} dengan argumen: {tool_args}{Style.RESET_ALL}")
                
                try:
                    result = tool_dictionary[tool_name](**tool_args)
                    print(f"{COLOR_TOOL}[Tool Output]: {result}{Style.RESET_ALL}")
                    
                    agent.add_tool_call(tool_call_id, result)
                    
                except Exception as e:
                    error_message = f"Tool execution failed: {str(e)}"
                    print(f"{COLOR_TOOL}[Tool Output - Error]: {error_message}{Style.RESET_ALL}")
                    agent.add_tool_call(tool_call_id, error_message)
                
                print(f"{COLOR_THINKING}[AI Thinking]: Menganalisis hasil tool untuk jawaban akhir...{Style.RESET_ALL}")
            else:
                print("\n" + "="*50 + "\n")
                break
        
        agent.payload['messages'] = []
    
    except KeyboardInterrupt:
        print(f"\n{COLOR_AGENT}Goodbye!")
        break
    except Exception as e:
        print(f"\n{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
        agent.payload['messages'] = []
        continue