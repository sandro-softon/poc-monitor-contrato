import smtplib
from email.message import EmailMessage
from src.config import Config

class EmailSender:
    def __init__(self):
        self.host = Config.SMTP_HOST
        self.port = Config.SMTP_PORT
        self.user = Config.SMTP_USER
        self.password = Config.SMTP_PASS
        self.use_tls = Config.SMTP_USE_TLS
        self.email_from = Config.EMAIL_FROM
        self.email_to = Config.EMAIL_TO

    def send_alert(self, alerts: list):
        if not alerts:
            print("Nenhum alerta para ser enviado.")
            return

        subject = f"[ALERTA] Monitoramento de Contratos - {len(alerts)} contrato(s) exigem atenção"
        
        # --- PLAIN TEXT BODY ---
        body = "RELATÓRIO GERENCIAL DE MONITORAMENTO DE CONTRATOS\n"
        body += "=" * 60 + "\n\n"
        body += f"Identificamos {len(alerts)} contrato(s) que exigem atenção imediata devido a prazos ou volumetria.\n\n"
        
        for alert in alerts:
            bd = alert.get('acessos_breakdown', {})
            body += f"■ INSTITUIÇÃO: {alert['instituicao']} ({alert['codigo']})\n"
            body += f"  Número do Contrato...: {alert.get('contrato', '-')}\n"
            body += f"  Serviço Contratado...: {alert.get('servico', '-')}\n"
            body += f"  Motivo do Alerta.....: {', '.join(alert['motivos'])}\n"
            body += f"  Período de Corte.....: {alert['inicio']} à {alert['vencimento']} ({alert['dias_restantes']} dias restantes)\n"
            body += f"  Acessos no Período...:\n"
            body += f"       Individual: {bd.get('Individual', 0):>10}\n"
            body += f"             Lote: {bd.get('Lote', 0):>10}\n"
            body += f"              API: {bd.get('Api', bd.get('API', 0)):>10}\n"
            body += f"            Total: {alert['acessos_realizados']:>10}  de  {alert['limite_total']} acessos\n"
            body += f"  Consumo do Limite....: {alert['perc_uso']}%\n"
            body += "\n" + "-" * 60 + "\n\n"
            
        body += "Este é um e-mail automático do sistema de monitoramento.\n"
        
        # --- HTML BODY ---
        html_body = f"""\
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 700px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="background-color: #2c3e50; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">Relatório Gerencial de Monitoramento</h2>
                </div>
                <div style="padding: 20px;">
                    <p style="font-size: 16px;">Identificamos <strong>{len(alerts)} contrato(s)</strong> que exigem atenção imediata devido a prazos ou volumetria de uso.</p>
        """
        
        for alert in alerts:
            bd = alert.get('acessos_breakdown', {})
            html_body += f"""\
                    <div style="margin-bottom: 25px; padding: 20px; border: 1px solid #ddd; border-left: 5px solid #e74c3c; border-radius: 6px; background-color: #fcfcfc;">
                        <h3 style="margin-top: 0; color: #2980b9; border-bottom: 1px solid #eee; padding-bottom: 10px;">🏢 {alert['instituicao']} ({alert['codigo']})</h3>
                        <table style="width: 100%; border-collapse: collapse; font-size: 15px;">
                            <tr><td style="padding: 6px 0; width: 180px; color: #555;"><strong>Número do Contrato:</strong></td><td>{alert.get('contrato', '-')}</td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Serviço Contratado:</strong></td><td><span style="background-color: #eaf4fb; color: #2980b9; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{alert.get('servico', '-')}</span></td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Motivo do Alerta:</strong></td><td><span style="color: #e74c3c; font-weight: bold;">{', '.join(alert['motivos'])}</span></td></tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Período de Corte:</strong></td><td>{alert['inicio']} à {alert['vencimento']} <span style="color: #e67e22;">({alert['dias_restantes']} dias restantes)</span></td></tr>
                            <tr>
                              <td style="padding: 6px 0; color: #555; vertical-align: top;"><strong>Acessos no Período:</strong></td>
                              <td>
                                <table style="border-collapse: collapse; font-size: 14px; width: auto;">
                                  <tr><td style="padding: 2px 12px 2px 0; color: #555;">Individual:</td><td style="text-align: right; padding: 2px 0;">{bd.get('Individual', 0)}</td></tr>
                                  <tr><td style="padding: 2px 12px 2px 0; color: #555;">Lote:</td><td style="text-align: right; padding: 2px 0;">{bd.get('Lote', 0)}</td></tr>
                                  <tr><td style="padding: 2px 12px 2px 0; color: #555;">API:</td><td style="text-align: right; padding: 2px 0;">{bd.get('Api', bd.get('API', 0))}</td></tr>
                                  <tr style="border-top: 1px solid #ccc;">
                                    <td style="padding: 4px 12px 2px 0; color: #333;">Total:</td>
                                    <td style="text-align: right; padding: 4px 0;">{alert['acessos_realizados']} <span style="color: #888; font-weight: normal;">de {alert['limite_total']}</span></td>
                                  </tr>
                                </table>
                              </td>
                            </tr>
                            <tr><td style="padding: 6px 0; color: #555;"><strong>Consumo do Limite:</strong></td><td><strong>{alert['perc_uso']}%</strong></td></tr>
                        </table>
                    </div>
            """
            
        html_body += """\
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
            print(f"E-mail de alerta enviado com sucesso para {', '.join(self.email_to)}.")
        except Exception as e:
            print(f"Erro ao enviar o e-mail via SMTP ({self.host}:{self.port}): {e}")
            print("\nConteúdo do e-mail que não pôde ser enviado (Fallback Log):")
            print(body)
