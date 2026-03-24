import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Banco de Dados
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_NAME = os.getenv("DB_DATABASE", "meubanco")
    
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
    
    # Regras/Thresholds Default
    ALERT_DAYS_BEFORE_EXPIRATION = int(os.getenv("ALERT_DAYS_BEFORE_EXPIRATION", 30))
    ALERT_USAGE_PERCENTAGE = float(os.getenv("ALERT_USAGE_PERCENTAGE", 0.8))
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

