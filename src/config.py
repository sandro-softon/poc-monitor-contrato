import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()

class Config:
    # Banco de Dados
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_NAME = os.getenv("DB_DATABASE", "meubanco")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}/{DB_NAME}",
    )
    
    # Email
    SMTP_HOST = os.getenv("SMTP_HOST", "127.0.0.1")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 25))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "False").lower() in ("true", "1", "yes")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "monitor@localhost")
    EMAIL_TO = os.getenv("EMAIL_TO", "admin@localhost").split(",")
    
    # Caminhos
    EXCEL_PATH = os.getenv("EXCEL_PATH", "docs/Softon_Controle de acessos_clientes_VF.xlsx")
    # Optional: especificar nome da sheet a ser lida (ex: 'Sheet1')
    EXCEL_SHEET = os.getenv("EXCEL_SHEET", None)
    CONTRACT_SOURCE = os.getenv("CONTRACT_SOURCE", "excel").strip().lower()
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", 30))
    WEB_ADMIN_USER = os.getenv("WEB_ADMIN_USER", "admin")
    WEB_ADMIN_PASS = os.getenv("WEB_ADMIN_PASS", "admin")
    WEB_AUTH_TOKEN = os.getenv("WEB_AUTH_TOKEN", "dev-admin-token")
    
    # Regras/Thresholds Default
    ALERT_DAYS_BEFORE_EXPIRATION = int(os.getenv("ALERT_DAYS_BEFORE_EXPIRATION", 30))
    ALERT_USAGE_PERCENTAGE = float(os.getenv("ALERT_USAGE_PERCENTAGE", 0.8))
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
