from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Numeric, String, Text, text
from sqlalchemy.dialects.mysql import BIT, INTEGER, LONGTEXT, TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Instituicao(Base):
    __tablename__ = "TB_INSTITUICAO"

    codigo_instituicao: Mapped[Decimal] = mapped_column(
        "COD_INSTITUICAO", Numeric(10, 0), primary_key=True
    )
    nome_instituicao: Mapped[str] = mapped_column("NOME_INSTITUICAO", String(100))
    numero_contrato: Mapped[Optional[str]] = mapped_column("NUM_CONTRATO", String(50))
    dt_ini: Mapped[Optional[datetime]] = mapped_column("DT_INI", DateTime)
    dt_fim: Mapped[Optional[datetime]] = mapped_column("DT_FIM", DateTime)
    num_ac_contratados: Mapped[Optional[int]] = mapped_column(
        "NUM_AC_CONTRATADOS", INTEGER
    )
    tp_acessos: Mapped[str] = mapped_column("TP_ACESSOS", String(50))
    flg_mens: Mapped[Optional[str]] = mapped_column("FLG_MENS", String(50))
    txt_mens: Mapped[Optional[str]] = mapped_column("TXT_MENS", LONGTEXT)
    status: Mapped[Optional[int]] = mapped_column("STATUS", TINYINT(1))
    numero_linhas_resultado: Mapped[Optional[Decimal]] = mapped_column(
        "NUMERO_LINHAS_RESULTADO", Numeric(18, 0)
    )
    tp_informacao: Mapped[Optional[int]] = mapped_column("TP_INFORMACAO", INTEGER)
    produtos: Mapped[str] = mapped_column("PRODUTOS", String(80))
    fl_power_match: Mapped[bytes] = mapped_column("FL_POWER_MATCH", BIT(1))
    qt_linhas_power_match: Mapped[Optional[int]] = mapped_column(
        "QT_LINHAS_POWER_MATCH", INTEGER
    )
    dt_inicio_pesquisa: Mapped[Optional[str]] = mapped_column(
        "DT_INICIO_PESQUISA", String(30)
    )
    dt_fim_pesquisa: Mapped[Optional[str]] = mapped_column(
        "DT_FIM_PESQUISA", String(30)
    )
    tp_algoritmo_solr: Mapped[Optional[int]] = mapped_column(
        "TP_ALGORITMO_SOLR", TINYINT(4)
    )
    txt_valid_ip: Mapped[Optional[str]] = mapped_column("TXT_VALID_IP", String(500))
    fl_pesquisa_individual: Mapped[int] = mapped_column(
        "FL_PESQUISA_INDIVUDUAL", TINYINT(1)
    )
    fl_dados_complementares: Mapped[int] = mapped_column(
        "FL_DADOS_COMPLEMENTARES", TINYINT(1)
    )
    qt_monitoramento: Mapped[int] = mapped_column("QT_MONITORAMENTO", INTEGER)


class Contrato(Base):
    __tablename__ = "TB_CONTRATO"

    id_contrato: Mapped[int] = mapped_column("ID_CONTRATO", BigInteger, primary_key=True)
    codigo_instituicao: Mapped[Decimal] = mapped_column(
        "COD_INSTITUICAO", Numeric(10, 0)
    )
    cod_compartilhado: Mapped[Optional[Decimal]] = mapped_column(
        "COD_COMPARTILHADO", Numeric(10, 0)
    )
    numero_contrato: Mapped[Optional[str]] = mapped_column("NUM_CONTRATO", String(50))
    dt_ini: Mapped[datetime] = mapped_column("DT_INI", DateTime)
    dt_fim: Mapped[datetime] = mapped_column("DT_FIM", DateTime)
    dt_corte_inicial: Mapped[datetime] = mapped_column("DT_CORTE_INICIAL", DateTime)
    frequencia_corte: Mapped[str] = mapped_column("FREQUENCIA_CORTE", String(20))
    servicos_contratados: Mapped[str] = mapped_column(
        "SERVICOS_CONTRATADOS", String(80)
    )
    num_ac_contratados: Mapped[Optional[int]] = mapped_column(
        "NUM_AC_CONTRATADOS", INTEGER
    )
    fl_acessos_ilimitados: Mapped[int] = mapped_column(
        "FL_ACESSOS_ILIMITADOS", TINYINT(1)
    )
    valor_excedente: Mapped[Optional[Decimal]] = mapped_column(
        "VALOR_EXCEDENTE", Numeric(12, 2)
    )
    fl_monitorar_contrato: Mapped[int] = mapped_column(
        "FL_MONITORAR_CONTRATO", TINYINT(1)
    )
    dt_criacao: Mapped[datetime] = mapped_column(
        "DT_CRIACAO", DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    dt_atualizacao: Mapped[Optional[datetime]] = mapped_column(
        "DT_ATUALIZACAO", DateTime, onupdate=datetime.now
    )
