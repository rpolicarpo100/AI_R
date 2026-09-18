# 🐳 Opção B Docker — 1 Comando — SEM Rust, SEM Python

**Docker instalado (v29.7.2) mas daemon não rodando — erro que tiveste:**

```
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
O sistema não conseguiu localizar o ficheiro especificado.
```

**Isso significa:** Docker CLI instalado, mas Docker Desktop (engine) não está rodando. Precisa abrir Docker Desktop e esperar ficar VERDE.

---

## 🔧 FIX RÁPIDO — Faz AGORA (2 min)

### Passo 1 — Abrir Docker Desktop manualmente

1. **Abre menu Iniciar → procura "Docker Desktop" → clica para abrir**
2. **Espera 30-60s** — primeira vez demora
3. **Olha canto inferior esquerdo** — deve ficar **VERDE "Engine running" / "Running"**
4. Se ficar vermelho ou não abre, vai para Passo 2

### Passo 2 — Fix WSL (se Passo 1 falhar)

Abre **PowerShell como ADMIN** (botão direito no PowerShell → Run as administrator) e faz:

```powershell
wsl --update
wsl --shutdown
```

Depois **abre Docker Desktop novamente** e espera ficar VERDE.

Ou executa o script fix que criei:

```cmd
cd AI_R
docker-fix-windows.bat
```
- Roda como ADMIN se possível (botão direito → Run as administrator)
- Faz wsl --update + wsl --shutdown + abre Docker Desktop + espera 30s

### Passo 3 — Testar se daemon agora roda

No CMD:

```cmd
docker ps
```

- Se mostrar lista (mesmo vazia) → **OK, daemon rodando**
- Se ainda der erro `failed to connect` → repete Passo 1-2, reinicia PC

### Passo 4 — Start AI Provider OS

Depois de `docker ps` funcionar:

```cmd
cd AI_R
docker-start.bat
```

Ou:

```cmd
docker compose up --build
```

- Primeira vez 2-5 min (baixa python:3.11-slim + node:20-alpine)
- Depois rápido (cache)

---

## 🌐 Acessar (depois de docker compose up)

- **Frontend:** http://localhost:3000 — CHAT AI | Settings
- **Backend:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health → `{"status":"healthy","providers":200}`

---

## 🆘 Troubleshooting Completo Windows

### Erro que tiveste:

```
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
O sistema não conseguiu localizar o ficheiro especificado.
```

**Causa:** Docker Desktop não está aberto/rodando. Docker CLI (`docker --version`) funciona, mas engine não.

**Fix:**

1. **Abre Docker Desktop manualmente** — não basta ter instalado, precisa estar rodando
2. **Espera ficar VERDE Running** — canto inferior esquerdo
3. **Se não ficar verde:**
   - PowerShell ADMIN:
     ```powershell
     wsl --update
     wsl --shutdown
     ```
   - Abre Docker Desktop novamente
   - Se ainda falhar, reinicia PC

4. **Verifica:**
   ```cmd
   docker ps
   ```
   Deve funcionar (lista vazia OK). Se funcionar, faz `docker-start.bat`

### Outros erros:

**Docker não encontrado:**
```
docker: command not found
```
- Instala Docker Desktop https://www.docker.com/products/docker-desktop/
- Reinicia PC

**Porta 8000/3000 ocupada:**
```cmd
docker compose down
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

**Build falha:**
```cmd
docker system prune -a
docker compose up --build --no-cache
```

**Frontend não abre:**
- Aguarda 30s — backend healthcheck 30s
- `docker compose logs -f backend`
- Testa http://localhost:8000/health primeiro

**WSL2 erro:**
```powershell
wsl --update
wsl --shutdown
```
Abre Docker Desktop novamente.

---

## 📊 Porquê Docker resolve teu erro pydantic-core

- Teu erro anterior: `Failed building wheel for pydantic-core` + precisa Rust no Windows Python 3.13
- **Docker usa `python:3.11-slim`** — tem wheels binários prontos, sem Rust
- `requirements.txt` flexível `>=` encontra wheels
- Sem venv, sem pip, sem Rust

---

## 🎯 Resumo — O que fazer AGORA

```cmd
# 1. Abre Docker Desktop manualmente (menu Iniciar)
# Espera ficar VERDE Running (30-60s)

# 2. Testa se daemon roda
docker ps

# 3. Se docker ps falhar, fix WSL
docker-fix-windows.bat
# Ou PowerShell ADMIN:
# wsl --update
# wsl --shutdown
# Abre Docker Desktop novamente

# 4. Quando docker ps funcionar
cd AI_R
docker-start.bat
# Ou
docker compose up --build

# 5. Abre
# http://localhost:3000
# http://localhost:8000/docs
```

---

**Faz Passo 1 agora: abre Docker Desktop e espera ficar VERDE, depois `docker ps` deve funcionar** 🐳
