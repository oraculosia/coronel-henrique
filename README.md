# Campanha 2026

Plataforma Streamlit + Supabase para parceiros, metas diárias e apoiadores.

O Supabase é a autoridade de autenticação e autorização. O Streamlit concentra fluxo e interface.

## Fase 1 — Fundação (atual)

Checklist:

1. Repositório e `.venv`
2. Projeto Supabase
3. `.env` a partir de `.env.example`
4. Schema em `sql/001_foundation.sql` (enums, tabelas, índices, RLS)
5. Auth com confirmação por e-mail / OTP
6. Template HTML em `supabase/templates/confirm_signup.html`
7. Primeiro `super_admin` via `scripts/bootstrap_super_admin.py`
   (William Eustáquio / cargo Desenvolvedor de IA / papel `super_admin`)
8. SMTP Hostinger no Supabase Auth (`supabase/SMTP_HOSTINGER.md`)
9. Página **Minha conta** para cada usuário editar os próprios dados

## Ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Preencha `SUPABASE_URL` com `https://<ref>.supabase.co` (não use connection string `postgresql://`).

## Testes da Fase 1

```powershell
pytest tests/test_phase1_foundation.py -q
```

Teste ao vivo (schema já aplicado no projeto):

```powershell
pytest tests/test_phase1_foundation.py -q -m live
```

## Próxima fase

Fase 2 — Autenticação (login, cadastro, OTP, sessão e guards) já está parcialmente no código. Só avançar depois dos testes desta fundação no verde.
