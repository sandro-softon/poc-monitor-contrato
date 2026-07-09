import logging
import pandas as pd
from collections import defaultdict
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


def _normalize_service(value: str) -> str:
    service = str(value).strip().lower()
    service_map = {
        "api": "API",
        "individual": "Individual",
        "lote": "Lote",
    }
    return service_map.get(service, str(value).strip())


def _normalize_limit(value):
    if value is None or pd.isna(value):
        return 0.0, False

    if isinstance(value, int | float):
        return float(value), False

    text = str(value).strip()
    if text.lower() in {"ilimitado", "ilimitada"}:
        return None, True

    try:
        return float(text.replace(".", "").replace(",", ".")), False
    except ValueError:
        return 0.0, False


class ContractAnalyzer:
    def __init__(self, excel_reader, access_reader):
        self.excel_reader = excel_reader
        self.access_reader = access_reader

    def analyze(self, full=False, institution_code: str | None = None):
        contracts = self.excel_reader.read_contracts()
        filter_code = _normalize_code(institution_code)

        now = datetime.now()
        today_start = datetime.combine(now.date(), datetime.min.time())
        data_referencia_datetime = today_start - timedelta(seconds=1)

        # Group contracts by instituicao
        groups = defaultdict(list)
        for contract in contracts:
            instituicao = _normalize_code(contract.get("Codigo Instituicao", ""))
            cod_compartilhado = _normalize_code(contract.get("Cod Compartilhado"))
            if filter_code and filter_code not in {instituicao, cod_compartilhado}:
                continue
            groups[instituicao].append(contract)

        alerts = []

        for instituicao, contract_list in groups.items():
            first = contract_list[0]
            nome = first.get("Nome Instituicao")
            numero_contrato = str(first.get("Numero Contrato", "")).strip()
            cod_compartilhado = first.get("Cod Compartilhado")
            dt_inicio = first.get("data de corte início")
            dt_fim = first.get("data de corte final")
            frequencia = str(first.get("Frequencia", "Anual")).strip().lower()

            if pd.isna(dt_fim) or pd.isna(dt_inicio):
                id_text = numero_contrato or instituicao or "n/a"
                logger.debug(
                    "[SKIP] Contrato %s pulado: dt_inicio=%s dt_fim=%s",
                    id_text, dt_inicio, dt_fim,
                )
                continue

            dt_inicio_ciclo, dt_fim_ciclo = get_current_cycle(
                dt_inicio, frequencia, data_referencia_datetime,
            )
            dt_fim_consulta = min(dt_fim_ciclo, today_start)
            data_referencia_corte = dt_fim_consulta - timedelta(days=1)
            codes = [instituicao]
            cod_compartilhado_norm = _normalize_code(cod_compartilhado)
            if cod_compartilhado_norm:
                codes.append(cod_compartilhado_norm)

            # Collect all services from the group
            all_servicos = set()
            max_limite_val = 0.0
            qualquer_ilimitado = False
            valor_excedente = None
            for contract in contract_list:
                servico_raw = str(contract.get("Serviços Contratados", "")).strip()
                for s in servico_raw.split(","):
                    all_servicos.add(_normalize_service(s.strip()))

                acessos = contract.get("acessos contratados", 0)
                lim, ilim = _normalize_limit(acessos)
                if ilim:
                    qualquer_ilimitado = True
                if not ilim and lim > max_limite_val:
                    max_limite_val = lim

                ve = contract.get("Valor Excedente")
                if ve is not None and not (isinstance(ve, float) and pd.isna(ve)):
                    valor_excedente = ve

            servicos_ordered = sorted(all_servicos)
            servicos_label = ", ".join(servicos_ordered)

            logger.info(
                "Processando: %s (%s) | Serviços: %s | Contrato: %s",
                nome, instituicao, servicos_label, numero_contrato,
            )
            logger.debug(
                "[CORTE] Referência=%s | Início período=%s | Fim período=%s | Fim contrato=%s | SQL < %s | Códigos: %s",
                data_referencia_corte.strftime("%Y-%m-%d"),
                dt_inicio_ciclo.strftime("%Y-%m-%d"),
                data_referencia_corte.strftime("%Y-%m-%d"),
                dt_fim.strftime("%Y-%m-%d"),
                dt_fim_consulta.strftime("%Y-%m-%d"),
                ", ".join(codes),
            )
            dias_restantes = (dt_fim_ciclo - data_referencia_datetime).days
            alerta_vencimento = False
            if 0 <= dias_restantes <= Config.ALERT_DAYS_BEFORE_EXPIRATION:
                alerta_vencimento = True
            elif dias_restantes < 0:
                alerta_vencimento = True

            # Single access query per group
            acessos_por_servico = self.access_reader.get_accesses_by_service(
                codes,
                dt_inicio_ciclo.strftime("%Y-%m-%d %H:%M:%S"),
                dt_fim_ciclo.strftime("%Y-%m-%d %H:%M:%S"),
            )
            acessos_breakdown = {
                s: acessos_por_servico.get(s, 0) for s in servicos_ordered
            }
            acessos_realizados = sum(acessos_breakdown.values())

            limite_ilimitado = qualquer_ilimitado
            limite_total = None if qualquer_ilimitado else max_limite_val

            if filter_code:
                logger.info(
                    "Acessos consolidados: Individual=%s | Lote=%s | API=%s | Total=%s de %s",
                    acessos_por_servico.get("Individual", 0),
                    acessos_por_servico.get("Lote", 0),
                    acessos_por_servico.get("API", 0),
                    acessos_realizados,
                    limite_total if not limite_ilimitado else "ILIMITADO",
                )

            alerta_uso = False
            perc_uso = 0.0
            if not limite_ilimitado and limite_total > 0:
                perc_uso = acessos_realizados / limite_total
                if perc_uso >= Config.ALERT_USAGE_PERCENTAGE:
                    alerta_uso = True

            if alerta_vencimento or alerta_uso or full:
                motivos = [
                    m for m, v in [
                        ("Próximo da Data de Corte Final", alerta_vencimento),
                        ("Volume Elevado/Excedido", alerta_uso),
                    ]
                    if v
                ]
                if full and not motivos:
                    motivos = ["Relatório Completo"]

                alerts.append({
                    "instituicao": nome,
                    "codigo": instituicao,
                    "contrato": numero_contrato,
                    "servico": servicos_label,
                    "frequencia": frequencia.title(),
                    "inicio_original": dt_inicio.strftime("%d/%m/%Y"),
                    "vencimento_original": dt_fim.strftime("%d/%m/%Y"),
                    "data_referencia_corte": data_referencia_corte.strftime("%d/%m/%Y"),
                    "inicio_periodo_corte": dt_inicio_ciclo.strftime("%d/%m/%Y"),
                    "fim_periodo_corte": data_referencia_corte.strftime("%d/%m/%Y"),
                    "fim_contrato": dt_fim.strftime("%d/%m/%Y"),
                    "inicio_ciclo": dt_inicio_ciclo.strftime("%d/%m/%Y"),
                    "fim_ciclo": data_referencia_corte.strftime("%d/%m/%Y"),
                    "dias_restantes": dias_restantes,
                    "limite_total": limite_total,
                    "limite_ilimitado": limite_ilimitado,
                    "acessos_realizados": acessos_realizados,
                    "acessos_breakdown": acessos_breakdown,
                    "perc_uso": round(perc_uso * 100, 2),
                    "valor_excedente": valor_excedente,
                    "motivos": motivos,
                })
                logger.debug(
                    "[ALERTA] %s: %s/%s (%.1f%%) | Venc: %s | Dias: %s",
                    servicos_label,
                    acessos_realizados,
                    limite_total if not limite_ilimitado else "∞",
                    perc_uso * 100,
                    dt_fim.strftime("%Y-%m-%d"),
                    dias_restantes,
                )
            else:
                logger.debug(
                    "[OK] %s: %s/%s (%.1f%%) | Venc: %s | Dias: %s",
                    servicos_label,
                    acessos_realizados,
                    limite_total if not limite_ilimitado else "∞",
                    perc_uso * 100,
                    dt_fim.strftime("%Y-%m-%d"),
                    dias_restantes,
                )

        return alerts
