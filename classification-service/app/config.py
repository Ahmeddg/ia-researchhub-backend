import os
import psycopg2

class Settings:
    """
    Application settings loaded from environment variables and the database.
    Static settings (DB URL, API keys) are loaded from env.
    Dynamic settings (thresholds) are loaded from the database with a TTL cache.
    """
    def __init__(self):
        # --- STATIC SETTINGS ---
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5433/article_db"
        )
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "allenai/specter2_base")
        self.EMBEDDING_DIM: int = 768
        self.OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "https://api.ollama.com/api/generate")
        self.OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "28de8464911240dc9b29591a0c97bf12.XcaV7bc7kZnrTnqwfMHuxR66")
        self.OLLAMA_MODEL_NAME: str = os.getenv("OLLAMA_MODEL_NAME", "gemma3:4b-cloud")
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # --- DYNAMIC SETTINGS CACHE ---
        self._cache = {}
        self._last_refresh = 0
        self._cache_ttl = 60  # seconds

        # Default dynamic settings fallback
        self._defaults = {
            "SIMILARITY_THRESHOLD": ("0.75", float),
            "SOFT_SIMILARITY_THRESHOLD": ("0.65", float),
            "HDBSCAN_MIN_CLUSTER_SIZE": ("2", int),
            "STABLE_ID_SIMILARITY_THRESHOLD": ("0.85", float),
            "DYNAMIC_THRESHOLD_MULTIPLIER": ("0.90", float),
            "MIN_ASSIGNMENT_THRESHOLD": ("0.60", float),
            "MAX_ASSIGNMENT_THRESHOLD": ("0.88", float),
            "PENDING_RECLUSTER_ATTEMPTS": ("3", int),
            "RECLUSTER_MIN_NEW_PAPERS": ("200", int),
            "RECLUSTER_PENDING_THRESHOLD": ("50", int),
            "RECLUSTER_MAX_INTERVAL_HOURS": ("24", int),
            "CAH_L1_COUNT": ("8", int),
            "CAH_L2_COUNT": ("30", int),
            "CORRECTION_WINDOW_DAYS": ("30", int),
            "CORRECTION_RATE_HIGH": ("0.10", float),
            "CORRECTION_RATE_LOW": ("0.02", float),
            "THRESHOLD_TIGHTEN_DELTA": ("0.02", float),
            "THRESHOLD_RELAX_DELTA": ("0.01", float),
        }

    def _get_dynamic(self, key: str):
        import time
        now = time.time()
        if now - self._last_refresh > self._cache_ttl:
            self._refresh_cache()
            self._last_refresh = now
            
        if key in self._cache:
            val_str = self._cache[key]
            type_func = self._defaults[key][1]
            return type_func(val_str)
            
        # Fallback to defaults or env
        default_val, type_func = self._defaults[key]
        env_val = os.getenv(key, default_val)
        return type_func(env_val)

    def _refresh_cache(self):
        try:
            conn = psycopg2.connect(self.DATABASE_URL)
            with conn.cursor() as cur:
                # We check if table exists first to avoid crashing on startup before init_db
                cur.execute("SELECT to_regclass('public.system_config');")
                if cur.fetchone()[0] is not None:
                    cur.execute("SELECT key, value FROM system_config;")
                    for row in cur.fetchall():
                        self._cache[row[0]] = row[1]
        except Exception:
            pass
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    # --- DYNAMIC PROPERTIES ---
    @property
    def SIMILARITY_THRESHOLD(self) -> float: return self._get_dynamic("SIMILARITY_THRESHOLD")
    @property
    def SOFT_SIMILARITY_THRESHOLD(self) -> float: return self._get_dynamic("SOFT_SIMILARITY_THRESHOLD")
    @property
    def HDBSCAN_MIN_CLUSTER_SIZE(self) -> int: return self._get_dynamic("HDBSCAN_MIN_CLUSTER_SIZE")
    @property
    def STABLE_ID_SIMILARITY_THRESHOLD(self) -> float: return self._get_dynamic("STABLE_ID_SIMILARITY_THRESHOLD")
    @property
    def DYNAMIC_THRESHOLD_MULTIPLIER(self) -> float: return self._get_dynamic("DYNAMIC_THRESHOLD_MULTIPLIER")
    @property
    def MIN_ASSIGNMENT_THRESHOLD(self) -> float: return self._get_dynamic("MIN_ASSIGNMENT_THRESHOLD")
    @property
    def MAX_ASSIGNMENT_THRESHOLD(self) -> float: return self._get_dynamic("MAX_ASSIGNMENT_THRESHOLD")
    @property
    def PENDING_RECLUSTER_ATTEMPTS(self) -> int: return self._get_dynamic("PENDING_RECLUSTER_ATTEMPTS")
    @property
    def RECLUSTER_MIN_NEW_PAPERS(self) -> int: return self._get_dynamic("RECLUSTER_MIN_NEW_PAPERS")
    @property
    def RECLUSTER_PENDING_THRESHOLD(self) -> int: return self._get_dynamic("RECLUSTER_PENDING_THRESHOLD")
    @property
    def RECLUSTER_MAX_INTERVAL_HOURS(self) -> int: return self._get_dynamic("RECLUSTER_MAX_INTERVAL_HOURS")
    @property
    def CAH_L1_COUNT(self) -> int: return self._get_dynamic("CAH_L1_COUNT")
    @property
    def CAH_L2_COUNT(self) -> int: return self._get_dynamic("CAH_L2_COUNT")
    @property
    def CORRECTION_WINDOW_DAYS(self) -> int: return self._get_dynamic("CORRECTION_WINDOW_DAYS")
    @property
    def CORRECTION_RATE_HIGH(self) -> float: return self._get_dynamic("CORRECTION_RATE_HIGH")
    @property
    def CORRECTION_RATE_LOW(self) -> float: return self._get_dynamic("CORRECTION_RATE_LOW")
    @property
    def THRESHOLD_TIGHTEN_DELTA(self) -> float: return self._get_dynamic("THRESHOLD_TIGHTEN_DELTA")
    @property
    def THRESHOLD_RELAX_DELTA(self) -> float: return self._get_dynamic("THRESHOLD_RELAX_DELTA")

    def get_all_dynamic_configs(self):
        """Helper to get all configs for the API"""
        configs = {}
        for key in self._defaults:
            configs[key] = self._get_dynamic(key)
        return configs

settings = Settings()
