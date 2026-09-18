from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# P22 — SQLite optimizations for faster connections: WAL mode, cache size, synchronous NORMAL, temp store MEMORY
# Rigoroso: não perde funcionalidade, apenas otimiza ligações
# WAL mode allows concurrent reads/writes, 10x faster for many small queries (providers/models per request)
# cache_size -64000 = 64MB cache, synchronous NORMAL = faster, temp_store MEMORY = faster
# Pooling: for SQLite, use StaticPool or QueuePool with check_same_thread False + 20 connections

is_sqlite = "sqlite" in settings.DATABASE_URL

connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}

# P0 + P22 — Engine with pooling and optimizations — P0 uses central policy
try:
    from .policy import (
        DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE,
        DB_CACHE_SIZE_MB, DB_MMAP_SIZE_MB
    )
    db_pool_size = DB_POOL_SIZE
    db_max_overflow = DB_MAX_OVERFLOW
    db_pool_timeout = DB_POOL_TIMEOUT
    db_pool_recycle = DB_POOL_RECYCLE
    db_cache_kb = -DB_CACHE_SIZE_MB * 1000
    db_mmap = DB_MMAP_SIZE_MB * 1024 * 1024
    print(f"[DB P0] Loaded policy: pool_size={db_pool_size} max_overflow={db_max_overflow} cache={DB_CACHE_SIZE_MB}MB mmap={DB_MMAP_SIZE_MB}MB")
except Exception as e:
    print(f"[DB P0] Policy load failed {e}, using P22 defaults")
    db_pool_size = 10
    db_max_overflow = 20
    db_pool_timeout = 30
    db_pool_recycle = 3600
    db_cache_kb = -64000
    db_mmap = 268435456

# P22 — Engine with pooling and optimizations
if is_sqlite:
    from sqlalchemy.pool import QueuePool
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        poolclass=QueuePool,
        pool_size=db_pool_size,
        max_overflow=db_max_overflow,
        pool_timeout=db_pool_timeout,
        pool_recycle=db_pool_recycle,
        pool_pre_ping=True,
        echo=False
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute(f"PRAGMA cache_size={db_cache_kb};")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        cursor.execute(f"PRAGMA mmap_size={db_mmap};")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
        print(f"[DB] P0+P22 SQLite pragmas set: WAL, cache {abs(db_cache_kb)//1000}MB, synchronous NORMAL, temp MEMORY, mmap {db_mmap//1024//1024}MB, FK ON, pool {db_pool_size}+{db_max_overflow}")
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_timeout=db_pool_timeout,
        pool_recycle=db_pool_recycle,
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from ..models.database_models import Provider, Model, RequestLog, BenchmarkResult
    from ..models.agent_models import AgentDB, SkillDB, AgentCompetency, LoopTask
    from ..models.project_models import Project, ProjectGeneration
    Base.metadata.create_all(bind=engine)
    # P3 Performance + P22 — DB indexes for 726 models query + context_window
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_providers_status ON providers(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_models_test_count ON models(test_count)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_models_status ON models(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(timestamp)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_benchmark_results_provider_model ON benchmark_results(provider_id, model_id)"))
            # P22 — New indexes for faster routing: context_window, coding_score, overall_score
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_models_context ON models(context_window)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_models_coding ON models(coding_score)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_models_overall ON models(overall_score)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_providers_latency ON providers(avg_latency_ms)"))
            conn.commit()
            print("[DB] Indexes created - P3 Performance + P22 context, coding, overall, latency")
    except Exception as e:
        print(f"[DB] Index creation failed (optional): {e}")
