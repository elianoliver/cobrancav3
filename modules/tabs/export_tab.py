from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QFrame, QPushButton, QHBoxLayout,
    QMessageBox, QComboBox, QCheckBox, QGroupBox, QFileDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon
import pandas as pd
import os

from modules.tabs.base_tab import BaseTab
from modules.styles_fix import StyleManager, AppColors
from modules.config_manager import ConfigManager
from modules.data_processor import filter_users_by_category, generate_json_file


class ExportTab(BaseTab):
    """Aba para exportação dos dados processados em diferentes formatos."""

    # Sinais específicos desta aba
    export_completed = pyqtSignal(str, str)  # tipo, caminho

    def __init__(self, parent=None):
        self.config_manager = ConfigManager()
        self.unified_data = None
        self.categories = None
        super().__init__(parent)

    def setup_ui(self):
        """Configura a interface da aba de exportação."""
        # Cabeçalho
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 10)

        header = QLabel("Exportação de Dados")
        StyleManager.configure_header_label(header)
        header_layout.addWidget(header)

        description = QLabel(
            "Exporte os dados processados em diferentes formatos para uso em outros sistemas."
        )
        StyleManager.configure_subheader_label(description)
        header_layout.addWidget(description)

        self.layout.addWidget(header_container)

        # Mensagem quando não há dados
        self.no_data_label = QLabel(
            "Carregue e unifique os relatórios na aba de importação antes de exportar."
        )
        self.no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        StyleManager.configure_subheader_label(self.no_data_label)
        self.layout.addWidget(self.no_data_label)

        # Container principal para opções de exportação (inicialmente oculto)
        self.export_options_container = QFrame()
        self.export_options_container.setVisible(False)
        options_layout = QVBoxLayout(self.export_options_container)

        # 1. Opções de Filtro
        filter_group = QGroupBox("Filtrar Dados")
        filter_layout = QVBoxLayout(filter_group)

        # Tipo de usuário
        user_type_container = QWidget()
        user_type_layout = QHBoxLayout(user_type_container)
        user_type_layout.setContentsMargins(0, 0, 0, 0)

        user_type_label = QLabel("Tipo de Usuário:")
        user_type_layout.addWidget(user_type_label)

        self.user_type_combo = QComboBox()
        self.user_type_combo.addItem("Todos os Usuários", "all")
        self.user_type_combo.addItem("Apenas com Multas", "multas")
        self.user_type_combo.addItem("Apenas com Pendências", "pendencias")
        self.user_type_combo.addItem("Com Multas e Pendências", "ambos")
        self.user_type_combo.addItem("Com Chaves Emprestadas", "chaves")
        user_type_layout.addWidget(self.user_type_combo)

        filter_layout.addWidget(user_type_container)

        # Opção para incluir apenas usuários com email
        self.only_with_email = QCheckBox("Incluir apenas usuários com email")
        self.only_with_email.setChecked(True)
        filter_layout.addWidget(self.only_with_email)

        options_layout.addWidget(filter_group)

        # 2. Opções de Formato
        format_group = QGroupBox("Formato de Exportação")
        format_layout = QVBoxLayout(format_group)

        format_container = QWidget()
        format_layout_h = QHBoxLayout(format_container)
        format_layout_h.setContentsMargins(0, 0, 0, 0)

        format_label = QLabel("Formato:")
        format_layout_h.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItem("Excel (.xlsx)", "xlsx")
        self.format_combo.addItem("CSV (.csv)", "csv")
        self.format_combo.addItem("JSON (.json)", "json")
        format_layout_h.addWidget(self.format_combo)

        format_layout.addWidget(format_container)

        # Opção para agrupar por categoria
        self.group_by_category = QCheckBox("Agrupar por categoria no Excel (diferentes abas)")
        self.group_by_category.setChecked(True)
        self.group_by_category.setEnabled(True)
        format_layout.addWidget(self.group_by_category)

        # Conectar eventos para habilitar/desabilitar opções
        self.format_combo.currentIndexChanged.connect(self.update_format_options)

        options_layout.addWidget(format_group)

        # 3. Botões de Ação
        actions_container = QFrame()
        actions_layout = QHBoxLayout(actions_container)

        self.export_button = QPushButton("Exportar Dados")
        self.export_button.setObjectName("exportButton")
        StyleManager.configure_button(self.export_button, 'primary')
        self.export_button.clicked.connect(self.export_data)
        actions_layout.addWidget(self.export_button)

        options_layout.addWidget(actions_container)

        # Adicionar container de opções ao layout principal
        self.layout.addWidget(self.export_options_container)
        self.layout.addStretch()

    def update_data(self, unified_data=None, categories=None):
        """Atualiza os dados exibidos na aba."""
        if unified_data is not None:
            self.unified_data = unified_data
            self.no_data_label.setVisible(False)
            self.export_options_container.setVisible(True)

        if categories is not None:
            self.categories = categories

    def update_format_options(self):
        """Atualiza as opções disponíveis com base no formato selecionado."""
        current_format = self.format_combo.currentData()

        # Habilitar/desabilitar opções específicas de Excel
        excel_specific = (current_format == "xlsx")
        self.group_by_category.setEnabled(excel_specific)

        # Se não for Excel, desativar agrupamento
        if not excel_specific:
            self.group_by_category.setChecked(False)

    def export_data(self):
        """Exporta os dados no formato selecionado."""
        if self.unified_data is None or len(self.unified_data) == 0:
            self.show_message_box(
                "Erro",
                "Não há dados para exportar. Carregue e unifique os relatórios primeiro.",
                QMessageBox.Icon.Warning
            )
            return

        # Obter configurações selecionadas
        user_type = self.user_type_combo.currentData()
        only_with_email = self.only_with_email.isChecked()
        export_format = self.format_combo.currentData()
        group_by_category = self.group_by_category.isChecked() and export_format == "xlsx"

        # Aplicar filtros aos dados
        filtered_data = self.apply_filters(user_type, only_with_email)

        if filtered_data.empty:
            self.show_message_box(
                "Aviso",
                "Nenhum dado corresponde aos filtros selecionados.",
                QMessageBox.Icon.Information
            )
            return

        # Solicitar local para salvar o arquivo
        default_dir = self.config_manager.get_value('ultimo_diretorio', '')
        file_filter = self.get_file_filter(export_format)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Arquivo",
            os.path.join(default_dir, f"dados_exportados.{export_format}"),
            file_filter
        )

        if not file_path:
            return  # Usuário cancelou

        # Salvar o diretório para uso futuro
        self.config_manager.set_value('ultimo_diretorio', os.path.dirname(file_path))

        # Exportar baseado no formato
        try:
            if export_format == "xlsx":
                self.export_to_excel(filtered_data, file_path, group_by_category)
            elif export_format == "csv":
                filtered_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif export_format == "json":
                if not file_path.endswith('.json'):
                    file_path += '.json'
                generate_json_file(filtered_data, file_path)

            self.show_message_box(
                "Sucesso",
                f"Dados exportados com sucesso para {file_path}",
                QMessageBox.Icon.Information
            )

            # Emitir sinal de exportação completa
            self.export_completed.emit(export_format, file_path)

        except Exception as e:
            self.show_message_box(
                "Erro",
                f"Erro ao exportar dados: {str(e)}",
                QMessageBox.Icon.Critical
            )

    def apply_filters(self, user_type, only_with_email):
        """Aplica os filtros selecionados aos dados."""
        # Criar uma cópia para não modificar os dados originais
        filtered_data = self.unified_data.copy()

        # Filtrar por tipo de usuário
        if user_type != "all":
            # Obtém os codes dos usuários que correspondem ao filtro
            user_codes = filter_users_by_category(filtered_data, user_type)

            # Filtra o dataframe para incluir apenas esses códigos
            if user_codes:
                filtered_data = filtered_data[filtered_data['Código da pessoa'].isin(user_codes)]
            else:
                # Se não houver usuários correspondentes, retorna DataFrame vazio
                return pd.DataFrame()

        # Filtrar por presença de email
        if only_with_email:
            filtered_data = filtered_data[
                filtered_data['E-mail'].notna() &
                (filtered_data['E-mail'].str.strip() != '')
            ]

        return filtered_data

    def export_to_excel(self, data, file_path, group_by_category):
        """Exporta os dados para um arquivo Excel."""
        if not group_by_category:
            # Exportação simples sem agrupamento
            data.to_excel(file_path, index=False, sheet_name='Dados')
            return

        # Exportação com agrupamento por categorias
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Aba com todos os dados
            data.to_excel(writer, index=False, sheet_name='Todos os Dados')

            # Filtrar por relatório
            rel86 = data[data['Relatório'] == 'rel86']
            if not rel86.empty:
                rel86.to_excel(writer, index=False, sheet_name='Multas')

            rel76 = data[data['Relatório'] == 'rel76']
            if not rel76.empty:
                rel76.to_excel(writer, index=False, sheet_name='Pendências')

            # Filtrar usuários que têm chaves
            chaves_df = data[data['Número chave'].notna() & (data['Número chave'].str.strip() != "")]
            if not chaves_df.empty:
                chaves_df.to_excel(writer, index=False, sheet_name='Chaves')

    def get_file_filter(self, format_type):
        """Retorna o filtro para o diálogo de arquivos baseado no formato."""
        if format_type == "xlsx":
            return "Excel Files (*.xlsx)"
        elif format_type == "csv":
            return "CSV Files (*.csv)"
        elif format_type == "json":
            return "JSON Files (*.json)"
        return "All Files (*.*)"