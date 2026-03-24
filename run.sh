#!/bin/bash

# Exibe mensagem de início
echo "===================================================="
echo "Iniciando Processo de Monitoramento de Contratos"
echo "Data/Hora: $(date '+%Y-%m-%d %H:%M:%S')"
echo "===================================================="

# Verifica se o uv está instalado
if ! command -v uv &> /dev/null
then
    echo "Erro: 'uv' não encontrado. Por favor, instale o uv para prosseguir."
    exit 1
fi

# Executa a rotina via uv
PYTHONPATH=. uv run src/main.py

# Captura o status de saída
STATUS=$?

echo "===================================================="
if [ $STATUS -eq 0 ]; then
    echo "Processo finalizado com sucesso."
else
    echo "Ocorreu um erro durante a execução (Status: $STATUS)."
fi
echo "===================================================="
