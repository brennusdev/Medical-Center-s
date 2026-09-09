"""MED — Ferramenta de criptografia de arquivos de dados sensíveis.

CIFRA: Fernet (AES-128-CBC + HMAC-SHA256, autenticado — protege contra
leitura E contra adulteração). A chave NUNCA fica no disco em texto puro:
é derivada da senha-mestra via PBKDF2-HMAC-SHA256 (600k iterações, sal
aleatório por arquivo guardado no próprio cabeçalho do .enc).

Uso (PowerShell, na raiz do projeto):

    # Criptografar os dados importantes para a pasta secure_data/
    python scripts/secure_data.py encrypt

    # Listar o que está na pasta protegida
    python scripts/secure_data.py list

    # Restaurar um arquivo (pede a senha-mestra)
    python scripts/secure_data.py decrypt

REGRAS:
- A senha-mestra é pedida interativamente (getpass) — nunca em argumento de
  comando (o histórico do shell vazaria).
- Se `MED_DATA_PASSWORD` estiver definida no ambiente, é usada (para CI/scripts),
  mas isso NÃO é recomendado em máquinas de desenvolvimento.
- O .enc é autenticado: senha errada ou arquivo alterado → falha, sem dados
  parciais.
"""

from __future__ import annotations

import getpass
import os
import sys
from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parent.parent
SECURE_DIR = ROOT / "secure_data"
PBKDF2_ITERATIONS = 600_000

# Arquivos de dados sensíveis do projeto (relativos à raiz).
TARGET_FILES = [
    Path("Backend/medical_center.db"),
    Path("Backend/.coverage"),
]


def _password() -> str:
    env = os.environ.get("MED_DATA_PASSWORD")
    if env:
        return env
    pw = getpass.getpass("Senha-mestra dos dados: ")
    if len(pw) < 8:
        print("ERRO: senha muito curta (mínimo 8 caracteres).")
        sys.exit(1)
    return pw


def _fernet(password: str, salt: bytes) -> Fernet:
    key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return Fernet(urlsafe_b64encode(key))


def encrypt() -> None:
    SECURE_DIR.mkdir(exist_ok=True)
    pw = _password()
    for target in TARGET_FILES:
        src = ROOT / target
        if not src.exists():
            print(f"[skip] {target} (não existe)")
            continue
        salt = os.urandom(16)
        token = _fernet(pw, salt).encrypt(src.read_bytes())
        # Cabeçalho: "MEDENC1" + sal + token. O sal é público por design.
        out = SECURE_DIR / (src.name + ".enc")
        out.write_bytes(b"MEDENC1" + salt + token)
        print(f"[ok] {target} -> secure_data/{out.name} ({out.stat().st_size} bytes)")


def decrypt() -> None:
    pw = _password()
    for enc_file in sorted(SECURE_DIR.glob("*.enc")):
        blob = enc_file.read_bytes()
        if not blob.startswith(b"MEDENC1") or len(blob) < 7 + 16:
            print(f"[skip] {enc_file.name} (formato desconhecido)")
            continue
        salt = blob[7:23]
        token = blob[23:]
        try:
            data = _fernet(pw, salt).decrypt(token)
        except InvalidToken:
            print(f"[FALHA] {enc_file.name}: senha errada ou arquivo adulterado")
            continue
        dest = ROOT / "Backend" / enc_file.name.removesuffix(".enc")
        dest.write_bytes(data)
        print(f"[ok] {enc_file.name} -> {dest.relative_to(ROOT)} ({len(data)} bytes)")


def list_files() -> None:
    if not SECURE_DIR.exists():
        print("secure_data/ ainda não existe. Rode: python scripts/secure_data.py encrypt")
        return
    for f in sorted(SECURE_DIR.iterdir()):
        print(f"{f.name:40s} {f.stat().st_size:>10} bytes")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "encrypt":
        encrypt()
    elif cmd == "decrypt":
        decrypt()
    elif cmd == "list":
        list_files()
    else:
        print("Uso: python scripts/secure_data.py [encrypt|decrypt|list]")
