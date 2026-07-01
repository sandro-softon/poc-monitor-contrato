import logging
import math
import smtplib
from email.message import EmailMessage
from src.config import Config


logger = logging.getLogger(__name__)


def _format_brl(value) -> str:
    if _is_missing(value):
        return "-"

    text = str(value).strip()
    if not text:
        return "-"

    try:
        normalized = text.replace("R$", "").replace(" ", "")
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")

        amount = float(normalized)
    except (ValueError, TypeError):
        return "-"

    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def _format_number(value, decimal_places: int = 0) -> str:
    if _is_missing(value):
        return "-"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    formatted = f"{number:,.{decimal_places}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_limit(alert: dict) -> str:
    if alert.get("limite_ilimitado"):
        return "∞"

    value = alert.get("limite_total")
    if _is_missing(value):
        return "-"
    decimal_places = 0 if float(value).is_integer() else 2
    return _format_number(value, decimal_places)


def _format_usage(alert: dict) -> str:
    if alert.get("limite_ilimitado"):
        return "-"
    return f"{_format_number(alert['perc_uso'], 2)}%"


def _format_limit_html(alert: dict) -> str:
    if alert.get("limite_ilimitado"):
        return '<span style="font-size: 200%; font-weight: bold; line-height: 0; vertical-align: -0.15em;">∞</span>'
    return _format_limit(alert)


class EmailSender:
    def __init__(self):
        self.host = Config.SMTP_HOST
        self.port = Config.SMTP_PORT
        self.user = Config.SMTP_USER
        self.password = Config.SMTP_PASS
        self.use_tls = Config.SMTP_USE_TLS
        self.email_from = Config.EMAIL_FROM
        self.email_to = Config.EMAIL_TO

    def send_alert(self, alerts: list, is_full_report=False):
        if not alerts:
            logger.info("Nenhum alerta para ser enviado.")
            return

        if is_full_report:
            subject = f"[RELATÓRIO] Monitoramento de Contratos - Relatório Completo ({len(alerts)} contrato(s))"
            header_text = f"Segue o relatório completo de monitoramento com todos os <strong>{len(alerts)} contrato(s)</strong> processados."
            plain_intro = f"RELATÓRIO COMPLETO DE MONITORAMENTO DE CONTRATOS\nIdentificamos {len(alerts)} contrato(s) processados.\n"
        else:
            subject = f"[ALERTA] Monitoramento de Contratos - {len(alerts)} contrato(s) exigem atenção"
            header_text = f"Identificamos <strong>{len(alerts)} contrato(s)</strong> que exigem atenção imediata devido a prazos ou volumetria de uso."
            plain_intro = f"RELATÓRIO GERENCIAL DE MONITORAMENTO DE CONTRATOS\nIdentificamos {len(alerts)} contrato(s) que exigem atenção imediata devido a prazos ou volumetria.\n"

        # --- PLAIN TEXT BODY ---
        body = plain_intro
        body += "=" * 60 + "\n\n"
        
        for alert in alerts:
            bd = alert.get('acessos_breakdown', {})
            limit_text = _format_limit(alert)
            inicio_periodo_corte = alert.get("inicio_periodo_corte", alert.get("inicio_ciclo", "-"))
            fim_periodo_corte = alert.get("fim_periodo_corte", alert.get("fim_ciclo", "-"))
            body += f"■ INSTITUIÇÃO: {alert['instituicao']} ({alert['codigo']})\n"
            body += f"  Número do Contrato...: {alert.get('contrato', '-')}\n"
            body += f"  Serviço Contratado...: {alert.get('servico', '-')}\n"
            body += f"  Motivo do Alerta/Ref.: {', '.join(alert['motivos'])}\n"
            body += f"  Período de Corte.....: {inicio_periodo_corte} à {fim_periodo_corte} ({alert['dias_restantes']} dias restantes)\n"
            body += f"  Tipo de Corte........: {alert.get('frequencia', '-')}\n"
            body += f"  Acessos no Período...:\n"
            for service_name, total in bd.items():
                body += f"  {service_name:>15}: {_format_number(total):>10}\n"
            body += f"            Total: {_format_number(alert['acessos_realizados']):>10}  de  {limit_text} acessos\n"
            body += f"  Consumo do Limite....: {_format_usage(alert)}\n"
            body += f"  Valor Excedente......: {_format_brl(alert.get('valor_excedente'))}\n"
            body += "\n" + "-" * 60 + "\n\n"
            
        body += "Este é um e-mail automático do sistema de monitoramento.\n"
        
        # --- HTML BODY ---
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 700px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background-color: #2c3e50; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">Relatório Gerencial de Monitoramento</h2>
                </div>
                <div style="padding: 20px;">
                    <p style="font-size: 16px;">{header_text}</p>
        """
        
        for alert in alerts:
            bd = alert.get('acessos_breakdown', {})
            limit_html = _format_limit_html(alert)
            inicio_periodo_corte = alert.get("inicio_periodo_corte", alert.get("inicio_ciclo", "-"))
            fim_periodo_corte = alert.get("fim_periodo_corte", alert.get("fim_ciclo", "-"))
            service_rows = "".join(
                f"""
                                  <tr><td style="padding: 2px 12px 2px 0; color: #555;">{service_name}:</td><td style="text-align: right; padding: 2px 0; min-width: 70px;">{_format_number(total)}</td><td style="padding: 2px 0 2px 8px;"></td></tr>
                """
                for service_name, total in bd.items()
            )
            # Dinamicamente muda a cor da borda se não for um alerta real
            # Vermelho (#e74c3c) para alertas reais, Azul (#3498db) para apenas relatório
            border_color = "#e74c3c" if any(m in ["Próximo da Data de Corte Final", "Volume Elevado/Excedido"] for m in alert['motivos']) else "#3498db"

            html_body += f"""
                    <div style="margin-bottom: 25px; padding: 20px; border: 1px solid #ddd; border-left: 5px solid {border_color}; border-radius: 6px; background-color: #fcfcfc;">
                        <h3 style="margin-top: 0; color: #2980b9; border-bottom: 1px solid #eee; padding-bottom: 10px;">🏢 {alert['instituicao']} ({alert['codigo']})</h3>
                        <table style="width: 100%; border-collapse: collapse; font-size: 15px;">
                            <tr><td style="padding: 6px 0; width: 180px; color: #555;"><strong>Número do Contrato:</strong></td><td>{alert.get('contrato', '-')}</td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Serviço Contratado:</strong></td><td><span style="background-color: #eaf4fb; color: #2980b9; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{alert.get('servico', '-')}</span></td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Motivo do Alerta/Ref:</strong></td><td><span style="color: {border_color}; font-weight: bold;">{', '.join(alert['motivos'])}</span></td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Período de Corte:</strong></td><td>{inicio_periodo_corte} à {fim_periodo_corte} <span style="color: #e67e22;">({alert['dias_restantes']} dias restantes)</span></td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Tipo de Corte:</strong></td><td>{alert.get('frequencia', '-')}</td></tr>
                            <tr>
                              <td style="padding: 6px 0; color: #555; vertical-align: top;"><strong>Acessos no Período:</strong></td>
                              <td>
                                <table style="border-collapse: collapse; font-size: 14px; width: auto;">
                                  {service_rows}
                                  <tr>
                                    <td style="padding: 2px 12px 2px 0; color: #555; font-weight: bold;">Total:</td>
                                    <td style="text-align: right; padding: 2px 0; min-width: 70px; font-weight: bold;">{_format_number(alert['acessos_realizados'])}</td>
                                    <td style="padding: 2px 0 2px 8px; font-weight: bold;">de {limit_html}</td>
                                  </tr>
                                </table>
                              </td>
                            </tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Consumo do Limite:</strong></td><td><strong>{_format_usage(alert)}</strong></td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Valor Excedente:</strong></td><td><strong>{_format_brl(alert.get('valor_excedente'))}</strong></td></tr>
                        </table>
                    </div>
            """
            
        html_body += """
                </div>
                <div style="background-color: #f1f2f6; padding: 15px; text-align: center; color: #7f8c8d; font-size: 12px; border-top: 1px solid #e0e0e0;">
                    Este é um e-mail automático gerado pelo sistema de monitoramento de contratos.<br>
                    Por favor, não responda a este e-mail.
                </div>
            </div>
          </body>
        </html>
        """
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = ", ".join(self.email_to)
        msg.set_content(body)
        msg.add_alternative(html_body, subtype='html')
        
        try:
            # Seleciona a classe SMTP correta (SMTP_SSL para porta 465, SMTP para outros)
            if self.port == 465:
                server_class = smtplib.SMTP_SSL
            else:
                server_class = smtplib.SMTP

            with server_class(self.host, self.port) as server:
                if self.use_tls and self.port != 465:
                    server.starttls()
                
                if self.user and self.password:
                    server.login(self.user, self.password)

                server.send_message(msg)
            logger.info(
                "E-mail de alerta enviado com sucesso para %s.",
                ", ".join(self.email_to),
            )
        except Exception as e:
            logger.error(
                "Erro ao enviar o e-mail via SMTP (%s:%s): %s",
                self.host,
                self.port,
                e,
            )
            logger.debug("Conteúdo do e-mail que não pôde ser enviado:\n%s", body)
