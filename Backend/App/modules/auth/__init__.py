"""MED V9 — Domínio de Autenticação e Autorização.

Responsabilidades do módulo:
- hash/verificação de senhas (nunca texto puro);
- emissão/validação de JWT (access + refresh);
- login, registro, renovação de token e "quem sou eu";
- dependencies reutilizáveis (get_current_user, require_role) para os routers.

Decisão de dependências: hash (PBKDF2-HMAC-SHA256, stdlib) e JWT (HS256,
stdlib hmac) são implementados em `security.py` SEM dependências externas,
cada função documentada. Em produção, podem ser trocados por passlib/PyJWT
sem alterar o contrato dos demais módulos.

Fluxo (documentado em ARCHITECTURE.md):
    Request → JWT → Current User → Role → Permission → Resource Ownership → Service
"""
