from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QFrame, QTextBrowser
)
from PyQt6.QtCore import pyqtSignal
import pandas as pd

from modules.tabs.base_tab import BaseTab
from modules.styles_fix import StyleManager
from modules.read_excel import get_summary

class SummaryTab(BaseTab):
    """Aba para exibição do resumo dos dados processados."""

    def __init__(self, parent=None):
        self.multas_df = None
        self.pendencias_df = None
        self.unified_data = None
        super().__init__(parent)

    def setup_ui(self):
        """Configura a interface da aba de resumo."""
        # Título e Subtítulo
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 10)

        # Cabeçalho
        header = QLabel("Resumo dos Dados")
        StyleManager.configure_header_label(header)
        header_layout.addWidget(header)

        # Descrição
        description = QLabel("Estatísticas gerais dos relatórios processados")
        StyleManager.configure_subheader_label(description)
        header_layout.addWidget(description)

        self.layout.addWidget(header_container)

        # Área de resumo em container estilizado
        summary_container = QFrame()
        summary_container.setObjectName("summaryContainer")
        summary_container_layout = QVBoxLayout(summary_container)

        self.summary_label = QTextBrowser()
        summary_container_layout.addWidget(self.summary_label)

        self.layout.addWidget(summary_container)

        # Aplicar estilos nativos
        StyleManager.configure_frame(summary_container, 'card')
        StyleManager.configure_text_edit(self.summary_label)

    def update_data(self, multas_df=None, pendencias_df=None, unified_data=None):
        """Atualiza os dados exibidos no resumo."""
        if multas_df is not None:
            self.multas_df = multas_df

        if pendencias_df is not None:
            self.pendencias_df = pendencias_df

        if unified_data is not None:
            self.unified_data = unified_data

        self.update_summary()

    def update_summary(self):
        """Atualiza o resumo com base nos arquivos carregados."""
        summary_html = "<div style='padding: 10px;'>"

        if self.multas_df is not None:
            summary_multas = get_summary(self.multas_df)
            summary_html += (
                "<h4>Relatório de Multas:</h4>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Linhas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_multas['num_rows']}</td></tr>"
                f"<tr><td>Pessoas únicas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_multas['num_unique_users']}</td></tr>"
                f"<tr><td>Total de multas:</td><td style='color: #f57c00; font-weight: bold;'>R$ {summary_multas['total_fines'] if isinstance(summary_multas['total_fines'], (int, float)) else 0:.2f}</td></tr>"
                "</table>"
            )

        if self.pendencias_df is not None:
            summary_pendencias = get_summary(self.pendencias_df)
            summary_html += (
                "<h4>Relatório de Pendências:</h4>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Linhas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_pendencias['num_rows']}</td></tr>"
                f"<tr><td>Pessoas únicas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_pendencias['num_unique_users']}</td></tr>"
                "</table>"
            )

        if self.unified_data is not None:
            # Encontrar a coluna correta para contagem de usuários
            if 'Código da pessoa' in self.unified_data.columns and not self.unified_data['Código da pessoa'].isna().all():
                total_users = self.unified_data['Código da pessoa'].nunique()
            else:
                total_users = 0  # Valor padrão se não encontrar coluna válida

            summary_html += (
                "<h4>Dados Unificados:</h4>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Total de registros:</td><td style='color: #2e7d32; font-weight: bold;'>{len(self.unified_data)}</td></tr>"
                f"<tr><td>Total de usuários:</td><td style='color: #2e7d32; font-weight: bold;'>{total_users}</td></tr>"
                "</table>"
            )

        summary_html += "</div>"
        self.summary_label.setHtml(summary_html)