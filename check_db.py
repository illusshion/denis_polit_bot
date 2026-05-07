import asyncio
from pathlib import Path

import asyncpg


def _read_postgres_url() -> str:
    env_path = Path("bot_template/.env")
    kv: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        kv[k.strip()] = v.strip()

    url = kv.get("POSTGRES_URL", "")
    if "postgresql+asyncpg://" in url:
        return "postgresql://" + url.split("postgresql+asyncpg://", 1)[1]
    return url


async def main() -> None:
    dsn = _read_postgres_url()
    if not dsn:
        raise SystemExit("POSTGRES_URL not found in bot_template/.env")

    conn = await asyncpg.connect(dsn)
    try:
        tables = await conn.fetch(
            """
            select table_schema, table_name
            from information_schema.tables
            where table_schema not in ('pg_catalog','information_schema')
              and table_type = 'BASE TABLE'
            order by 1, 2
            """
        )
        print(f"tables: {len(tables)}")

        stats = await conn.fetch(
            """
            select schemaname, relname, n_live_tup::bigint as approx_rows
            from pg_stat_user_tables
            order by approx_rows desc nulls last, schemaname, relname
            """
        )
        print("top tables by approx rows:")
        for r in stats[:30]:
            print(f"{r['schemaname']}.{r['relname']}\t~{r['approx_rows']}")

        nonempty = [r for r in stats if (r["approx_rows"] or 0) > 0]
        if nonempty:
            print("exact row counts (for tables with approx_rows > 0):")
            for r in nonempty[:20]:
                schema = r["schemaname"]
                table = r["relname"]
                q = f'SELECT COUNT(*)::bigint FROM "{schema}"."{table}"'
                n = await conn.fetchval(q)
                print(f'{schema}.{table}\t= {n}')
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

