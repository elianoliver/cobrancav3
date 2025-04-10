from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QFrame, QTextBrowser
)
from PyQt6.QtCore import pyqtSignal
import pandas as pd

from modules.tabs.base_tab import BaseTab
from modules.styles_fix import StyleManager
from modules.data_processor import categorize_users

class ResultsTab(BaseTab):
    """Aba para exibição dos resultados da unificação dos relatórios."""

    def __init__(self, parent=None):
        self.unified_data = None
        super().__init__(parent)

    def setup_ui(self):
        """Configura a interface da aba de resultados."""
        # Título da aba de resultados
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 10)

        title = QLabel("Resultados da Unificação")
        StyleManager.configure_header_label(title)
        title_layout.addWidget(title)

        subtitle = QLabel("Visualize os dados processados e estatísticas")
        StyleManager.configure_subheader_label(subtitle)
        title_layout.addWidget(subtitle)

        self.layout.addWidget(title_container)

        # Área de resultados em um container estilizado
        result_container = QFrame()
        result_container.setObjectName("resultContainer")
        result_layout = QVBoxLayout(result_container)

        self.result_area = QTextBrowser()
        self.result_area.setOpenExternalLinks(True)  # Permite abrir links
        result_layout.addWidget(self.result_area)

        self.layout.addWidget(result_container)

        # Aplicar estilos nativos
        StyleManager.configure_frame(result_container, 'card')
        StyleManager.configure_text_edit(self.result_area)

    def update_data(self, unified_data):
        """Atualiza os dados exibidos na aba com o dataframe unificado."""
        self.unified_data = unified_data
        self.display_unified_results()

    def display_unified_results(self):
        """Exibe os resultados da unificação em formato de dashboard"""
        if self.unified_data is None:
            return

        # Obter categorias e estatísticas
        categories = categorize_users(self.unified_data)

        # Calcular estatísticas para os botões
        df_rel86 = self.unified_data[self.unified_data['Relatório'] == 'rel86']
        df_rel76 = self.unified_data[self.unified_data['Relatório'] == 'rel76']

        # Contagens de pessoas únicas
        unique_users_rel86 = df_rel86['Código da pessoa'].nunique() if 'Código da pessoa' in df_rel86.columns else 0
        unique_users_rel76 = df_rel76['Código da pessoa'].nunique() if 'Código da pessoa' in df_rel76.columns else 0

        # Filtrar registros com chaves emprestadas
        chaves_df = self.unified_data[
            (~self.unified_data['Número chave'].isna()) &
            (self.unified_data['Número chave'].str.strip() != "")
        ]

        # Quantidade de pessoas únicas com chaves
        unique_users_chaves = chaves_df['Código da pessoa'].nunique() if 'Código da pessoa' in chaves_df.columns else 0

        # HTML simplificado para o dashboard com cards recolhíveis (sem tabelas de detalhes)
        dashboard_html = """
        <div style='font-family: Arial, sans-serif; padding: 20px;'>
            <h2 style='color: #2c3e50; text-align: center; margin-bottom: 25px;'>Dashboard de Relatórios</h2>

            <div style='display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;'>
                <!-- Card do Relatório 86 (recolhível) -->
                <div id="card_rel86" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; border: 1px solid #e0e0e0; overflow: hidden;'>
                    <!-- Cabeçalho do card (sempre visível) -->
                    <div style='background-color: #3498db; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; cursor: pointer;'
                         onclick="toggleCard('rel86_content', 'rel86_toggle')">
                        <div>
                            <h3 style='margin: 0; display: flex; align-items: center;'>
                                <span style='font-size: 24px; margin-right: 10px;'>📊</span>
                                Relatório 86 (Multas)
                            </h3>
                        </div>
                        <span id="rel86_toggle" style='font-size: 20px;'>▼</span>
                    </div>

                    <!-- Conteúdo do card (recolhível) -->
                    <div id="rel86_content" style='padding: 15px; display: block;'>
                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; '>
                            <ul style='list-style-type: none; padding-left: 0;'>
                                <li><strong>Número total de linhas:</strong> {rel86_linhas}</li>
                                <li><strong>Pessoas únicas no relatório:</strong> {rel86_unique_users}</li>
                                <li><strong>Pessoas únicas sem email:</strong> {rel86_pessoas_sem_email}</li>
                                <li><strong>Valor total de multas:</strong> R$ {rel86_total_multas:.2f}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Card do Relatório 76 (recolhível) -->
                <div id="card_rel76" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; border: 1px solid #e0e0e0; overflow: hidden;'>
                    <!-- Cabeçalho do card (sempre visível) -->
                    <div style='background-color: #e74c3c; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; cursor: pointer;'
                         onclick="toggleCard('rel76_content', 'rel76_toggle')">
                        <div>
                            <h3 style='margin: 0; display: flex; align-items: center;'>
                                <span style='font-size: 24px; margin-right: 10px;'>📚</span>
                                Relatório 76 (Pendências)
                            </h3>
                        </div>
                        <span id="rel76_toggle" style='font-size: 20px;'>▼</span>
                    </div>

                    <!-- Conteúdo do card (recolhível) -->
                    <div id="rel76_content" style='padding: 15px; display: block;'>
                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; '>
                            <ul style='list-style-type: none; padding-left: 0;'>
                                <li><strong>Número total de linhas:</strong> {rel76_linhas}</li>
                                <li><strong>Pessoas únicas no relatório:</strong> {rel76_unique_users}</li>
                                <li><strong>Pessoas únicas sem email:</strong> {rel76_pessoas_sem_email}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Card de Pessoas Sem Email (recolhível) -->
                <div id="card_sem_email" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; border: 1px solid #e0e0e0; overflow: hidden;'>
                    <!-- Cabeçalho do card (sempre visível) -->
                    <div style='background-color: #27ae60; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; cursor: pointer;'
                         onclick="toggleCard('sem_email_content', 'sem_email_toggle')">
                        <div>
                            <h3 style='margin: 0; display: flex; align-items: center;'>
                                <span style='font-size: 24px; margin-right: 10px;'>👤</span>
                                Pessoas Sem Email
                            </h3>
                        </div>
                        <span id="sem_email_toggle" style='font-size: 20px;'>▼</span>
                    </div>

                    <!-- Conteúdo do card (recolhível) -->
                    <div id="sem_email_content" style='padding: 15px; display: block;'>
                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; '>
                            <ul style='list-style-type: none; padding-left: 0;'>
                                <li><strong>Total de pessoas sem email:</strong> {sem_email}</li>
                                <li><strong>Pessoas do rel86 sem email:</strong> {rel86_pessoas_sem_email}</li>
                                <li><strong>Pessoas do rel76 sem email:</strong> {rel76_pessoas_sem_email}</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Card de Chaves Emprestadas (recolhível) -->
                <div id="card_chaves" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; border: 1px solid #e0e0e0; overflow: hidden;'>
                    <!-- Cabeçalho do card (sempre visível) -->
                    <div style='background-color: #f39c12; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; cursor: pointer;'
                         onclick="toggleCard('chaves_content', 'chaves_toggle')">
                        <div>
                            <h3 style='margin: 0; display: flex; align-items: center;'>
                                <span style='font-size: 24px; margin-right: 10px;'>🔑</span>
                                Chaves Emprestadas
                            </h3>
                        </div>
                        <span id="chaves_toggle" style='font-size: 20px;'>▼</span>
                    </div>

                    <!-- Conteúdo do card (recolhível) -->
                    <div id="chaves_content" style='padding: 15px; display: block;'>
                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; '>
                            <ul style='list-style-type: none; padding-left: 0;'>
                                <li><strong>Total de multas de chaves:</strong> {total_chaves}</li>
                                <li><strong>Pessoas com multas de chaves:</strong> {unique_users_chaves}</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Função para alternar a visibilidade do conteúdo do card
            function toggleCard(contentId, toggleId) {{
                var content = document.getElementById(contentId);
                var toggle = document.getElementById(toggleId);

                if (content.style.display === 'none') {{
                    content.style.display = 'block';
                    toggle.innerText = '▼';
                }} else {{
                    content.style.display = 'none';
                    toggle.innerText = '▶';
                }}
            }}
        </script>
        """

        # Formatar o HTML com as estatísticas
        html_formatado = dashboard_html.format(
            rel86_linhas=len(df_rel86),
            rel86_unique_users=unique_users_rel86,
            rel86_pessoas_sem_email=len(categories['rel86']['pessoas_sem_email']),
            rel86_total_multas=categories['rel86']['total_multas'],
            rel76_linhas=len(df_rel76),
            rel76_unique_users=unique_users_rel76,
            rel76_pessoas_sem_email=len(categories['rel76']['pessoas_sem_email']),
            rel76_atrasos=len(categories['rel76']['dias_atraso']),
            sem_email=len(categories['sem_email']['pessoas']),
            unique_users_chaves=unique_users_chaves,
            total_chaves=len(chaves_df)
        )

        # Atualizar a área de resultados com o HTML do dashboard
        self.result_area.setHtml(html_formatado)

    def show_welcome_message(self):
        """Exibe mensagem de boas-vindas na área de resultados."""
        StyleManager.configure_welcome_text_browser(self.result_area)