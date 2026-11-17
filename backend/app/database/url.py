def normalize_database_url(url: str) -> str:
    for scheme in ("postgres://", "postgresql://"):
        if url.startswith(scheme):
            return f"postgresql+psycopg://{url[len(scheme):]}"
    return url
