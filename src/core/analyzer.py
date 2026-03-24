import pandas as pd
from datetime import datetime
from src.config import Config


class ContractAnalyzer:
    def __init__(self, excel_reader, access_reader):
        self.excel_reader = excel_reader
        self.access_reader = access_reader

    def analyze(self, debug=False):
        contracts = self.excel_reader.read_contracts()
        alerts = []

        now = datetime.now()

        for contract in contracts:
            instituicao = str(contract.get("Codigo Instituicao", "")).strip()
            nome = contract.get("Nome Instituicao")
            numero_contrato = str(contract.get("Numero Contrato", "")).strip()
            servico = str(contract.get("Serviços Contratados", "")).strip()
            cod_compartilhado = contract.get("Cod Compartilhado")
            dt_inicio = contract.get("data de corte início")
            dt_fim = contract.get("data de corte final")
            acessos_contrato = contract.get("acessos contratados", 0)
            frequencia = str(contract.get("Frequencia", "Anual")).strip().lower()
            prazo_meses = contract.get("Prazo Contrato meses", 12)

            # Pula contratos sem data de término ou início válida
            if pd.isna(dt_fim) or pd.isna(dt_inicio):
                continue

            # Monta a lista de códigos (1 ou 2 elementos)
            codes = [instituicao]
            if cod_compartilhado and not pd.isna(cod_compartilhado):
                codes.append(str(cod_compartilhado).strip())

            print(f"Processando: {nome} ({instituicao}) | Serviço: {servico} | Contrato: {numero_contrato}")

            # Lógica de vencimento
            dias_restantes = (dt_fim - now).days
            alerta_vencimento = False
            if 0 <= dias_restantes <= Config.ALERT_DAYS_BEFORE_EXPIRATION:
                alerta_vencimento = True
            elif dias_restantes < 0:
                alerta_vencimento = True

            # Calcula limite total no período com base na frequência e prazo do contrato
            limite_total = acessos_contrato
            if frequencia == "mensal":
                limite_total = int(acessos_contrato * prazo_meses)
            elif frequencia == "semestral":
                limite_total = int(acessos_contrato * (prazo_meses / 6))

            # Busca de acessos por tipo de serviço (query UNION ALL)
            print(f"  > Consultando DB para {codes} entre {dt_inicio} e {dt_fim}...")
            acessos_por_servico = self.access_reader.get_accesses_by_service(
                codes,
                dt_inicio.strftime("%Y-%m-%d %H:%M:%S"),
                dt_fim.strftime("%Y-%m-%d %H:%M:%S"),
            )

            # Seleciona o valor correspondente ao(s) serviço(s) desta linha.
            # A célula pode conter múltiplos serviços separados por vírgula
            # (ex: "Individual, Lote, API"). Nesse caso, soma todos os valores.
            servicos_lista = [s.strip().title() for s in servico.split(",")]
            acessos_realizados = sum(
                acessos_por_servico.get(s, 0) for s in servicos_lista
            )

            print(f"  > Resultado ({', '.join(servicos_lista)}): {acessos_realizados} acessos. [API={acessos_por_servico['API']}, Individual={acessos_por_servico['Individual']}, Lote={acessos_por_servico['Lote']}]")

            # Lógica de estouro de uso
            alerta_uso = False
            perc_uso = 0.0
            if limite_total > 0:
                perc_uso = acessos_realizados / limite_total
                if perc_uso >= Config.ALERT_USAGE_PERCENTAGE:
                    alerta_uso = True

            if alerta_vencimento or alerta_uso:
                alerts.append(
                    {
                        "instituicao": nome,
                        "codigo": instituicao,
                        "contrato": numero_contrato,
                        "servico": servico,
                        "inicio": dt_inicio.strftime("%Y-%m-%d"),
                        "vencimento": dt_fim.strftime("%Y-%m-%d"),
                        "dias_restantes": dias_restantes,
                        "limite_total": limite_total,
                        "acessos_realizados": acessos_realizados,
                        "acessos_breakdown": acessos_por_servico,
                        "perc_uso": round(perc_uso * 100, 2),
                        "motivos": [
                            m
                            for m, v in [
                                ("Próximo da Data de Corte Final", alerta_vencimento),
                                ("Volume Elevado/Excedido", alerta_uso),
                            ]
                            if v
                        ],
                    }
                )
                if debug:
                    print(
                        f"  [ALERTA] {', '.join(servicos_lista)}: {acessos_realizados}/{limite_total} ({perc_uso:.1%}) | Venc: {dt_fim.strftime('%Y-%m-%d')} | Dias: {dias_restantes}"
                    )
            else:
                if debug:
                    print(
                        f"  [OK] {', '.join(servicos_lista)}: {acessos_realizados}/{limite_total} ({perc_uso:.1%}) | Venc: {dt_fim.strftime('%Y-%m-%d')} | Dias: {dias_restantes}"
                    )

        return alerts
