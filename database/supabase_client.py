import os
from dotenv import load_dotenv
from supabase import create_client
import httpx

# Carregar variáveis do .env
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

# Criar cliente Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError("⚠ ERRO: SUPABASE_URL ou SUPABASE_KEY não foram definidas no .env!")

# Primeiro cria o cliente normal
supabase = create_client(url, key)

# Depois configura o timeout no cliente interno
# Método 1: Direto no session
supabase.postgrest.session.timeout = httpx.Timeout(60.0)
