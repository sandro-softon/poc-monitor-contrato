import logging
import pandas as pd
from datetime import datetime, timedelta
from src.config import Config
from src.core.date_utils import get_current_cycle


logger = logging.getLogger(__name__)


def _normalize_code(value) -> str:
    if value is None or pd.isna(value):
        return ""

    text = str(value).strip()
    if text.endswith(".0"):
        return text[:-2]
    return text


class ContractAnalyzer:
    def __init__(self, excel_reader, access_reader):
        self.excel_reader = excel_reader
        self.access_reader = access_reader

    def analyze(self, full=False, institution_code: str | None = None):
        contracts = self.excel_reader.read_contracts()
        alerts = []
        filter_code = _normalize_code(institution_code)

        now = datetime.now()

        for contract in contracts:
            # ... (previous code remains same until alert check)
            instituicao = _normalize_code(contract.get("Codigo Instituicao", ""))
            nome = contract.get("Nome Instituicao")
            numero_contrato = str(contract.get("Numero Contrato", "")).strip()
            servico = str(contract.get("Serviços Contratados", "")).strip()
            cod_compartilhado = contract.get("Cod Compartilhado")
            dt_inicio = contract.get("data de corte início")
            dt_fim = contract.get("data de corte final")
            acessos_contrato = contract.get("acessos contratados", 0)
            frequencia = str(contract.get("Frequencia", "Anual")).strip().lower()

            cod_compartilhado_normalizado = _normalize_code(cod_compartilhado)
            if filter_code and filter_code not in {
                instituicao,
                cod_compartilhado_normalizado,
            }:
                continue

            if pd.isna(dt_fim) or pd.isna(dt_inicio):
                id_text = numero_contrato or instituicao or "n/a"
                logger.debug(
                    "[SKIP] Contrato %s pulado: dt_inicio=%s dt_fim=%s",
                    id_text,
                    dt_inicio,
                    dt_fim,
                )
                continue

            dt_inicio_ciclo, dt_fim_ciclo = get_current_cycle(dt_inicio, frequencia, now)
            codes = [instituicao]
            if cod_compartilhado_normalizado:
                codes.append(cod_compartilhado_normalizado)

            logger.info(
                "Processando: %s (%s) | Serviço: %s | Contrato: %s",
                nome,
                instituicao,
                servico,
                numero_contrato,
            )
            logger.debug(
                "[PERÍODO] Ciclo usado para contagem: %s até %s | Códigos: %s",
                dt_inicio_ciclo.strftime("%Y-%m-%d"),
                dt_fim_ciclo.strftime("%Y-%m-%d"),
                ", ".join(codes),
            )
            dias_restantes = (dt_fim_ciclo - now).days
            alerta_vencimento = False
            if 0 <= dias_restantes <= Config.ALERT_DAYS_BEFORE_EXPIRATION:
                alerta_vencimento = True
            elif dias_restantes < 0:
                alerta_vencimento = True

            limite_total = acessos_contrato
            acessos_por_servico = self.access_reader.get_accesses_by_service(
                codes,
                dt_inicio_ciclo.strftime("%Y-%m-%d %H:%M:%S"),
                dt_fim_ciclo.strftime("%Y-%m-%d %H:%M:%S"),
            )
            servicos_lista = [s.strip().title() for s in servico.split(",")]
            acessos_realizados = sum(
                acessos_por_servico.get(s, 0) for s in servicos_lista
            )
            if filter_code:
                logger.info(
                    "Acessos consolidados: Individual=%s | Lote=%s | API=%s | Total=%s de %s",
                    acessos_por_servico.get("Individual", 0),
                    acessos_por_servico.get("Lote", 0),
                    acessos_por_servico.get("API", 0),
                    acessos_realizados,
                    limite_total,
                )

            alerta_uso = False
            perc_uso = 0.0
            if limite_total > 0:
                perc_uso = acessos_realizados / limite_total
                if perc_uso >= Config.ALERT_USAGE_PERCENTAGE:
                    alerta_uso = True

            if alerta_vencimento or alerta_uso or full:
                motivos = [
                    m
                    for m, v in [
                        ("Próximo da Data de Corte Final", alerta_vencimento),
                        ("Volume Elevado/Excedido", alerta_uso),
                    ]
                    if v
                ]

                if full and not motivos:
                    motivos = ["Relatório Completo"]

                alerts.append(
                    {
                        "instituicao": nome,
                        "codigo": instituicao,
                        "contrato": numero_contrato,
                        "servico": servico,
                        "frequencia": frequencia.title(),
                        "inicio_original": dt_inicio.strftime("%d/%m/%Y"),
                        "vencimento_original": dt_fim.strftime("%d/%m/%Y"),
                        "inicio_ciclo": dt_inicio_ciclo.strftime("%d/%m/%Y"),
                        "fim_ciclo": (dt_fim_ciclo - timedelta(days=1)).strftime(
                            "%d/%m/%Y"
                        ),
                        "dias_restantes": dias_restantes,
                        "limite_total": limite_total,
                        "acessos_realizados": acessos_realizados,
                        "acessos_breakdown": acessos_por_servico,
                        "perc_uso": round(perc_uso * 100, 2),
                        "valor_excedente": contract.get("Valor Excedente"),
                        "motivos": motivos,
                    }
                )
                logger.debug(
                    "[ALERTA] %s: %s/%s (%.1f%%) | Venc: %s | Dias: %s",
                    ", ".join(servicos_lista),
                    acessos_realizados,
                    limite_total,
                    perc_uso * 100,
                    dt_fim.strftime("%Y-%m-%d"),
                    dias_restantes,
                )
            else:
                logger.debug(
                    "[OK] %s: %s/%s (%.1f%%) | Venc: %s | Dias: %s",
                    ", ".join(servicos_lista),
                    acessos_realizados,
                    limite_total,
                    perc_uso * 100,
                    dt_fim.strftime("%Y-%m-%d"),
                    dias_restantes,
                )

        return alerts
