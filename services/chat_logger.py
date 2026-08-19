"""
Serviço de Logging de Conversas do Chatbot (Atlas Web)
Registra todas as mensagens em arquivos JSONL diários para auditoria e melhoria do serviço.

Arquivos salvos em: data/chat_logs/YYYY-MM-DD.jsonl
Formato: Uma linha JSON por evento (mensagem de usuário ou resposta do assistente).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CHAT_LOGS_DIR = BASE_DIR / "data" / "chat_logs"


def _ensure_log_dir():
    """Garante que o diretório de logs existe."""
    CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log_message(
    session_id: str,
    role: str,
    content: str,
    model: str = "",
    provider: str = "",
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_estimate_brl: float = 0.0,
    tools_used: Optional[list] = None,
):
    """
    Registra uma mensagem no log diário JSONL.

    Args:
        session_id: ID da sessão do Streamlit (identifica o usuário/aba).
        role: 'user' ou 'assistant'.
        content: Conteúdo da mensagem.
        model: Nome do modelo LLM utilizado (ex: 'gpt-4o-mini').
        provider: Provider ativo ('openai' ou 'gemini').
        tokens_in: Tokens de entrada consumidos.
        tokens_out: Tokens de saída consumidos.
        cost_estimate_brl: Estimativa de custo em Reais.
        tools_used: Lista de nomes de tools chamadas pelo LLM (se houver).
    """
    _ensure_log_dir()

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "role": role,
        "content": content,
        "model": model,
        "provider": provider,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_estimate_brl": round(cost_estimate_brl, 6),
    }

    if tools_used:
        log_entry["tools_used"] = tools_used

    log_file = CHAT_LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
