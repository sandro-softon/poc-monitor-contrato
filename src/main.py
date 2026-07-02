import argparse
import logging
from src.config import Config
from src.readers.excel_reader import ContractReader
from src.readers.contract_db_reader import ContractDbReader
from src.readers.access_reader import AccessReader
from src.core.analyzer import ContractAnalyzer
from src.notifications.email_sender import EmailSender
from src.logging_config import setup_logging


logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Monitor de Contratos (POC).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python src/main.py --help
  ./run.sh --debug
  ./run.sh --test 12345
        """
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=Config.DEBUG,
        help="Ativa o modo de depuração (logs SQL e detalhes)."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Envia o relatório de todos os contratos, independente de alertas."
    )
    parser.add_argument(
        "--test",
        metavar="CODIGO_INSTITUICAO",
        help="Executa apenas a instituição informada, exibe detalhes e envia e-mail.",
    )
    parser.add_argument(
        "--src",
        choices=("excel", "db"),
        default=Config.CONTRACT_SOURCE,
        help="Fonte dos contratos: excel (padrão) ou db.",
    )

    args = parser.parse_args()
    setup_logging(debug=args.debug or bool(args.test))

    logger.info("Iniciando rotina de monitoramento de contratos...")

    # 1. Leitura
    contract_reader = (
        ContractDbReader() if args.src == "db" else ContractReader(Config.EXCEL_PATH)
    )
    access_reader = AccessReader()

    # 2. Análise
    logger.info("Lendo contratos da fonte '%s' e extraindo dados de consumo...", args.src)
    if args.debug:
        logger.info("[MODO DEBUG ATIVADO]")
    if args.full:
        logger.info("[MODO RELATÓRIO COMPLETO ATIVADO]")
    if args.test:
        logger.info("[MODO TESTE ATIVADO] Instituição: %s", args.test)

    analyzer = ContractAnalyzer(contract_reader, access_reader)
    full_report = args.full or bool(args.test)
    alerts = analyzer.analyze(full=full_report, institution_code=args.test)

    # 3. Notificação
    if alerts:
        if args.test:
            logger.info(
                "Gerando relatório de teste para %s contrato(s) da instituição %s.",
                len(alerts),
                args.test,
            )
        elif args.full:
            logger.info("Gerando relatório completo para %s contrato(s).", len(alerts))
        else:
            logger.info(
                "Encontrados %s contrato(s) com alerta de vencimento/uso.",
                len(alerts),
            )

        sender = EmailSender()
        sender.send_alert(alerts, is_full_report=full_report)
    else:
        if args.test:
            logger.info("Nenhum contrato encontrado para a instituição %s.", args.test)
        else:
            logger.info("Nenhum contrato encontrado ou processado.")

    logger.info("Rotina finalizada.")


if __name__ == "__main__":
    main()
