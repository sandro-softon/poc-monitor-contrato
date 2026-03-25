import argparse
from src.config import Config
from src.readers.excel_reader import ContractReader
from src.readers.access_reader import AccessReader
from src.core.analyzer import ContractAnalyzer
from src.notifications.email_sender import EmailSender

def main():
    parser = argparse.ArgumentParser(
        description="Monitor de Contratos (POC).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python src/main.py --help
  ./run.sh --debug
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
    
    args = parser.parse_args()
    
    print("Iniciando rotina de monitoramento de contratos...")
    
    # 1. Leitura
    excel_reader = ContractReader(Config.EXCEL_PATH)
    access_reader = AccessReader()
    
    # 2. Análise
    print("Lendo planilha e extraindo dados de consumo...")
    if args.debug:
        print("[MODO DEBUG ATIVADO]")
    if args.full:
        print("[MODO RELATÓRIO COMPLETO ATIVADO]")
        
    analyzer = ContractAnalyzer(excel_reader, access_reader)
    alerts = analyzer.analyze(debug=args.debug, full=args.full)
    
    # 3. Notificação
    if alerts:
        if args.full:
            print(f"Gerando relatório completo para {len(alerts)} contrato(s).")
        else:
            print(f"Encontrados {len(alerts)} contrato(s) com alerta de vencimento/uso.")
            
        sender = EmailSender()
        sender.send_alert(alerts, is_full_report=args.full)
    else:
        print("Nenhum contrato encontrado ou processado.")
        
    print("Rotina finalizada.")

if __name__ == "__main__":
    main()
