import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QFrame, QMessageBox, QProgressBar, QTabWidget, QFileDialog
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
import pandas as pd

# Importar as novas classes modularizadas
from modules.tabs import BaseTab, ImportTab, ResultsTab, SummaryTab, TemplateTab, ExportTab
from modules.read_excel import unify_dataframes
from modules.styles_fix import get_main_styles, StyleManager, AppColors
from modules.data_processor import generate_json_file, filter_users_by_category, categorize_users
from modules.config_manager import ConfigManager

# Constantes de estilo que agora usam AppColors
ACTION_CONTAINER_STYLE = f"""
    background-color: {AppColors.BACKGROUND.name()};
    border-radius: 6px;
    border: 1px solid {AppColors.BORDER.name()};
    margin-top: 20px;
    padding: 15px;
"""

class ExcelInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Cobrança - Biblioteca IFC")
        self.setMinimumSize(1000, 700)
        self.setContentsMargins(10, 10, 10, 10)

        # Inicializar o gerenciador de configuração
        self.config_manager = ConfigManager()

        # Variáveis de controle
        self.multas_df = None
        self.pendencias_df = None
        self.unified_data = None
        self.categories_count = None
        self.verificar_data = True
        self.multas_file = None
        self.pendencias_file = None

        # Configura a interface
        self.setup_ui()

        # Aplicar estilos usando a nova abordagem orientada a objetos
        self.apply_styles()

        # Mostrar mensagem de boas-vindas
        self.show_welcome_message()

    def setup_ui(self):
        """Configura a interface do usuário"""
        # Widget principal
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setCentralWidget(central_widget)

        # Adicionar cabeçalho com logo e título
        self.setup_header()

        # Criar tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Barra de progresso global (sempre visível, mas inicialmente vazia)
        self.progress_container = QFrame()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("progressBar")
        StyleManager.configure_progress_bar(self.progress_bar)

        progress_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_container)

        # Conectar sinal de mudança de tab para animação
        self.tabs.currentChanged.connect(self.animate_tab_change)

        # Setup das abas usando as novas classes modularizadas
        self.setup_tabs()

        # Adicionar as tabs ao layout principal
        main_layout.addWidget(self.tabs)

        # Adicionar rodapé com informações
        self.setup_footer()

        # Definir o tamanho inicial da janela
        self.resize(1280, 800)

        # Estilizar a aplicação
        self.setStyleSheet(get_main_styles())

    def setup_header(self):
        """Configura o cabeçalho da aplicação"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)

        # Logo/ícone da aplicação
        logo_label = QLabel("📚")
        logo_label.setObjectName("logoLabel")
        logo_label.setMinimumWidth(40)
        header_layout.addWidget(logo_label)

        # Título da aplicação
        title_label = QLabel("Biblioteca System")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)

        # Descrição da aplicação
        description_label = QLabel("Sistema de Gestão de Multas e Pendências")
        description_label.setObjectName("descriptionLabel")
        header_layout.addWidget(description_label, 1)

        # Adicionar o cabeçalho ao layout principal
        self.centralWidget().layout().addWidget(header_frame)

        # Aplicar estilos nativos com StyleManager
        StyleManager.configure_header_frame(header_frame)
        StyleManager.configure_logo_label(logo_label)

        # Configurações para o título e descrição usando QPalette em vez de CSS
        palette = title_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        title_label.setPalette(palette)

        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)

        # Configurar a descrição
        palette = description_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255, 204))  # white com 80% de opacidade
        description_label.setPalette(palette)

        font = description_label.font()
        font.setPointSize(14)
        description_label.setFont(font)

        # Armazenar referências para uso posterior
        self.headerFrame = header_frame
        self.logoLabel = logo_label

    def setup_footer(self):
        """Configura o rodapé da aplicação"""
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_layout = QHBoxLayout(footer_frame)

        # Texto de copyright/versão
        footer_text = QLabel("© 2023 Biblioteca System • v1.0.0")
        footer_text.setObjectName("footerText")
        footer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addWidget(footer_text)

        # Adicionar o rodapé ao layout principal
        self.centralWidget().layout().addWidget(footer_frame)

        # Aplicar estilos nativos usando StyleManager
        StyleManager.configure_footer_frame(footer_frame)
        StyleManager.configure_footer_text(footer_text)

        # Armazenar referências para uso posterior
        self.footerFrame = footer_frame
        self.footerText = footer_text

    def setup_tabs(self):
        """Configura todas as abas da aplicação utilizando as classes modularizadas"""
        # Instanciar e configurar a aba de importação
        self.import_tab = ImportTab(self)
        self.import_tab.files_loaded.connect(self.handle_files_loaded)
        self.import_tab.unify_requested.connect(self.unify_reports)
        self.import_tab.request_animate_progress.connect(self.animate_progress)
        self.import_tab.show_message.connect(self.show_message)
        self.tabs.addTab(self.import_tab, "📥 Importação")

        # Instanciar e configurar a aba de resultados
        self.results_tab = ResultsTab(self)
        self.results_tab.request_animate_progress.connect(self.animate_progress)
        self.results_tab.show_message.connect(self.show_message)
        self.tabs.addTab(self.results_tab, "📊 Resultados")

        # Instanciar e configurar a aba de resumo
        self.summary_tab = SummaryTab(self)
        self.summary_tab.request_animate_progress.connect(self.animate_progress)
        self.summary_tab.show_message.connect(self.show_message)
        self.tabs.addTab(self.summary_tab, "📋 Resumo")

        # Adicionar as abas restantes
        self.setup_template_tab()
        self.setup_export_tab()

    def animate_tab_change(self, index):
        """Anima a mudança de abas para uma experiência mais suave"""
        # Animar a barra de progresso como feedback visual
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i in range(101):
            QTimer.singleShot(i * 3, lambda v=i: self.progress_bar.setValue(v))

        QTimer.singleShot(350, lambda: self.progress_bar.setVisible(False))

    def handle_files_loaded(self, multas_df, pendencias_df, multas_file, pendencias_file):
        """Manipula o evento quando os arquivos são carregados na aba de importação"""
        self.multas_df = multas_df
        self.pendencias_df = pendencias_df
        self.multas_file = multas_file
        self.pendencias_file = pendencias_file

        # Atualizar a aba de resumo com os novos dados
        self.summary_tab.update_data(multas_df=multas_df, pendencias_df=pendencias_df)

    def unify_reports(self):
        """Unifica os dois relatórios em um único DataFrame"""
        if not (self.multas_df is not None and self.pendencias_df is not None):
            self.show_message(
                "Erro",
                "É necessário carregar os dois relatórios antes de unificá-los.",
                QMessageBox.Icon.Warning
            )
            return

        try:
            # Mostrar feedback visual
            self.animate_progress()

            # Chamar a função modularizada de unificação
            self.unified_data = unify_dataframes(self.multas_df, self.pendencias_df)

            # Gerar arquivo xlsx
            self.unified_data.to_excel('unificado.xlsx', index=False)

            # Atualizar o resumo com os dados unificados
            self.summary_tab.update_data(unified_data=self.unified_data)

            # Atualizar a aba de resultados
            self.results_tab.update_data(self.unified_data)

            # Mostrar template padrão (Apenas Multa)
            # [Será implementado quando configurarmos a aba de templates]
            if hasattr(self, 'template_tab'):
                self.template_tab.update_data(self.unified_data)

            # Habilitar a aba de exportação
            if hasattr(self, 'export_tab'):
                # Obter categorias de usuários
                self.categories_count = categorize_users(self.unified_data)
                self.export_tab.update_data(self.unified_data, self.categories_count)

            self.show_message("Sucesso", "Relatórios unificados com sucesso!")

            # Alternar para a aba de resultados
            self.tabs.setCurrentIndex(1)  # Índice 1 = aba de resultados

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro detalhado: {error_details}")
            self.show_message("Erro", f"Erro ao unificar relatórios: {str(e)}", QMessageBox.Icon.Critical)

    def animate_progress(self):
        """Anima a barra de progresso para feedback visual"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i in range(101):
            QTimer.singleShot(i * 10, lambda v=i: self.progress_bar.setValue(v))

        QTimer.singleShot(1100, lambda: self.progress_bar.setVisible(False))

    def show_message(self, title, message, icon=QMessageBox.Icon.Information):
        """Exibe um QMessageBox com estilo adequado"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

    def show_welcome_message(self):
        """Exibe mensagem de boas-vindas"""
        try:
            # Mostrar mensagem de boas-vindas na aba de resultados
            self.results_tab.show_welcome_message()
        except Exception as e:
            print(f"Erro ao exibir mensagem de boas-vindas: {e}")

    def apply_styles(self):
        """Aplica estilos usando abordagem nativa do PyQt6"""
        # Utilizamos o StyleManager para aplicar estilos nativos do Qt
        # Isso proporciona uma aparência mais integrada ao sistema e melhor desempenho

        # Configurar componentes individuais usando a classe StyleManager
        # Cabeçalho e rodapé
        if hasattr(self, 'headerFrame'):
            StyleManager.configure_header_frame(self.headerFrame)

        if hasattr(self, 'logoLabel'):
            StyleManager.configure_logo_label(self.logoLabel)

        if hasattr(self, 'footerFrame'):
            StyleManager.configure_footer_frame(self.footerFrame)

        if hasattr(self, 'footerText'):
            StyleManager.configure_footer_text(self.footerText)

        # Configurar abas
        if hasattr(self, 'tabs'):
            StyleManager.configure_tab_widget(self.tabs)

        # Configurar barra de progresso
        if hasattr(self, 'progress_bar'):
            StyleManager.configure_progress_bar(self.progress_bar)

    # [Outras funções que ainda precisamos manter]
    def setup_template_tab(self):
        """Configura a aba de templates de email"""
        # Instanciar e configurar a aba de templates
        self.template_tab = TemplateTab(self)
        self.template_tab.request_animate_progress.connect(self.animate_progress)
        self.template_tab.show_message.connect(self.show_message)
        self.template_tab.templates_updated.connect(self.handle_templates_updated)
        self.tabs.addTab(self.template_tab, "✉️ Templates")

    def setup_export_tab(self):
        """Configura a aba de exportação"""
        # Instanciar e configurar a aba de exportação
        self.export_tab = ExportTab(self)
        self.export_tab.request_animate_progress.connect(self.animate_progress)
        self.export_tab.show_message.connect(self.show_message)
        self.export_tab.export_completed.connect(self.handle_export_completed)
        self.tabs.addTab(self.export_tab, "📤 Exportação")

    def handle_templates_updated(self, templates):
        """Manipula o evento quando os templates são atualizados"""
        # Aqui podemos realizar qualquer ação necessária quando os templates são atualizados
        # Por exemplo, atualizar alguma configuração ou notificar outras abas
        print(f"Templates atualizados: {len(templates)} modelos")
        # O ConfigManager já salva os templates, então não precisamos fazer nada adicional aqui

    def handle_export_completed(self, format_type, file_path):
        """Manipula o evento quando a exportação é concluída"""
        # Aqui podemos realizar qualquer ação necessária quando a exportação é concluída
        # Por exemplo, mostrar uma mensagem adicional ou atualizar estatísticas
        print(f"Exportação concluída: {format_type} -> {file_path}")
        # Podemos adicionar alguma lógica adicional posteriormente, se necessário

def main():
    """Inicia a interface gráfica com PyQt6."""
    app = QApplication(sys.argv)

    # Aplicar o tema nativo para toda a aplicação
    StyleManager.apply_application_theme(app)

    window = ExcelInterface()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()