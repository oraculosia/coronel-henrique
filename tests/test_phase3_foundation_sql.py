from pathlib import Path

from src.config.settings import ROOT_DIR

SCHEMA_SQL_PATH = ROOT_DIR / "sql" / "004_partners_supporters_goals.sql"
PUBLIC_RESOLVE_SQL_PATH = ROOT_DIR / "sql" / "005_partners_public_resolve.sql"


def _schema_sql() -> str:
    return SCHEMA_SQL_PATH.read_text(encoding="utf-8")


def test_migration_files_exist() -> None:
    assert SCHEMA_SQL_PATH.exists()
    assert PUBLIC_RESOLVE_SQL_PATH.exists()


def test_partners_id_is_the_profile_id_not_a_separate_column() -> None:
    sql = _schema_sql().lower()
    assert "id uuid primary key references public.profiles (id)" in sql

    code_lines = [
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    ]
    assert "profile_id" not in "\n".join(code_lines)


def test_supporters_has_no_email_column_and_requires_whatsapp() -> None:
    sql = _schema_sql().lower()
    supporters_block = sql.split("create table if not exists public.supporters")[1]
    supporters_block = supporters_block.split(";")[0]
    assert "email" not in supporters_block
    assert "whatsapp text not null" in supporters_block
    assert "consent_lgpd" in supporters_block
    assert "source_utm" in supporters_block


def test_goal_status_enum_matches_live_values() -> None:
    sql = _schema_sql()
    assert "'active'" in sql
    assert "'achieved'" in sql
    assert "'expired'" in sql
    assert "'cancelled'" in sql


def test_public_insert_policy_requires_lgpd_and_validation_function() -> None:
    sql = _schema_sql().lower()
    policy_block = sql.split("create policy supporters_public_insert")[1]
    policy_block = policy_block.split("drop policy if exists supporters_partner_update_own")[0]
    assert "consent_lgpd = true" in policy_block
    assert "consent_at is not null" in policy_block
    assert "is_public_partner_signup_valid" in policy_block


def test_goal_increment_trigger_does_not_create_missing_goal_row() -> None:
    sql = _schema_sql().lower()
    function_block = sql.split(
        "create or replace function public.increment_partner_daily_goal"
    )[1]
    assert "update public.daily_goals" in function_block
    assert "insert into public.daily_goals" not in function_block


def test_public_resolve_policy_limits_columns_for_anon() -> None:
    sql = PUBLIC_RESOLVE_SQL_PATH.read_text(encoding="utf-8").lower()
    code_lines = [
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    ]
    code = "\n".join(code_lines)
    assert "to anon" in code
    assert "is_accepting_supporters = true" in code
    assert "telegram_chat_id" not in code
    assert "created_by" not in code
