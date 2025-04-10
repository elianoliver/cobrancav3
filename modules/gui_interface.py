import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QTextEdit,
    QMessageBox, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QSplitter,
    QGroupBox, QProgressBar, QRadioButton, QButtonGroup, QTabWidget, QGridLayout, QTabWidget, QTextBrowser, QDialog
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon, QPixmap, QCursor, QPalette, QColor
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
import pandas as pd
from modules.read_excel import read_excel_file, clean_column_names, get_summary, unify_dataframes
from modules.data_processor import generate_json_file, filter_users_by_category, categorize_users
from modules.styles_fix import get_drop_area_style, get_status_label_style
from modules.styles_fix import get_main_styles, get_welcome_html, get_categories_html
# Importar todas as classes de estilo do módulo styles_fix
from modules.styles_fix import StyleManager, AppColors
import json
from datetime import datetime

# Constantes de estilo que agora usam AppColors
CARD_STYLE = f"""
    border: 1px solid {AppColors.BORDER.name()};
    border-radius: 6px;
    background-color: {AppColors.CARD.name()};
    padding: 15px;
"""

HEADER_STYLE = f"""
    font-size: 24px;
    font-weight: bold;
    color: {AppColors.PRIMARY.name()};
"""

SUBHEADER_STYLE = f"""
    font-size: 14px;
    color: {AppColors.TEXT_LIGHT.name()};
"""

INSTRUCTION_CARD_STYLE = f"""
    background-color: {AppColors.INFO_LIGHT.name()};
    border-radius: 6px;
    border: 1px solid {AppColors.INFO_LIGHT.darker(110).name()};
    padding: 15px;
    margin-bottom: 20px;
"""

INFO_CARD_STYLE = f"""
    background-color: {AppColors.ACCENT_LIGHT.name()};
    border-radius: 6px;
    border: 1px solid {AppColors.ACCENT_LIGHT.darker(110).name()};
    padding: 20px;
    margin: 10px 0 20px 0;
"""

ACTION_CONTAINER_STYLE = f"""
    background-color: {AppColors.BACKGROUND.name()};
    border-radius: 6px;
    border: 1px solid {AppColors.BORDER.name()};
    margin-top: 20px;
    padding: 15px;
"""

class ConfigManager:
    """Gerencia a configuração da aplicação usando um arquivo JSON"""
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        """Carrega a configuração do arquivo ou cria uma nova se não existir"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar configuração: {e}")
                return self._create_default_config()
        else:
            return self._create_default_config()

    def _save_config(self, config=None):
        """Salva a configuração no arquivo"""
        if config is None:
            config = self.config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")

    def get_value(self, key, default=None):
        """Obtém um valor da configuração"""
        return self.config.get(key, default)

    def set_value(self, key, value):
        """Define um valor na configuração"""
        self.config[key] = value
        self._save_config()

    def _create_default_config(self):
        """Cria uma configuração padrão"""
        default_config = {
            'template_apenas_multa': '',
            'template_apenas_pendencia': '',
            'template_multa_e_pendencia': '',
            'ultimo_diretorio': ''
        }
        self._save_config(default_config)
        return default_config

class FileDropArea(QFrame):
    """Área de arrastar e soltar para arquivos Excel com identificação do tipo"""
    fileDropped = pyqtSignal(str, str)  # Sinal que emite caminho do arquivo e tipo

    def __init__(self, report_type="multas", parent=None):
        super().__init__(parent)
        self.setObjectName("dropArea")
        self.setMinimumHeight(150)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.report_type = report_type  # 'multas' ou 'pendencias'
        self.file_path = None
        self.setAcceptDrops(True)

        # Configurar tamanho mínimo para evitar elementos comprimidos
        self.setMinimumWidth(250)

        # Layout e componentes visuais
        self.setup_ui()

        # Aplicar estilo usando StyleManager
        StyleManager.configure_drop_area(self, self.report_type)

        # Timer para animar o highlight quando o mouse entra
        self.highlight_timer = QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.timeout.connect(self.reset_highlight)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Ícone diferente para cada tipo de relatório
        icon = "💰" if self.report_type == "multas" else "📚"
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setObjectName("dropIcon")
        layout.addWidget(self.icon_label)

        # Descrição do tipo de relatório
        title = "Relatório de Multas (86)" if self.report_type == "multas" else "Relatório de Pendências (76)"
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("dropTitle")
        layout.addWidget(self.title_label)

        # Instrução
        self.text_label = QLabel("Arraste o arquivo Excel aqui\nou clique para procurar")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)

        # Status do arquivo
        self.status_label = QLabel("Nenhum arquivo selecionado")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("fileStatusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Configurar o label de status usando StyleManager
        StyleManager.configure_status_label(self.status_label, False)

        # Adiciona espaçamento ao final
        layout.addStretch()

    def set_file(self, file_path):
        """Define o arquivo e atualiza o visual"""
        self.file_path = file_path
        if file_path:
            filename = os.path.basename(file_path)
            # Limita o tamanho do nome do arquivo para evitar que ultrapasse a largura do componente
            if len(filename) > 30:
                display_name = filename[:27] + "..."
            else:
                display_name = filename

            self.status_label.setText(f"Arquivo: {display_name}")
            # Atualizar o estilo do status_label usando StyleManager
            StyleManager.configure_status_label(self.status_label, True)
            self.text_label.setText("Clique para trocar o arquivo")

            # Destacar visualmente a borda para indicar seleção
            self.highlight_success()
        else:
            self.status_label.setText("Nenhum arquivo selecionado")
            # Atualizar o estilo do status_label usando StyleManager
            StyleManager.configure_status_label(self.status_label, False)
            self.text_label.setText("Arraste o arquivo Excel aqui\nou clique para procurar")

            # Restaurar o estilo original
            StyleManager.configure_drop_area(self, self.report_type)

    def mousePressEvent(self, event):
        """Quando clicado, abre diálogo para selecionar arquivo"""
        last_dir = ConfigManager().get_value('ultimo_diretorio', '')

        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Selecione o {self.title_label.text()}",
            last_dir,
            "Excel Files (*.xlsx *.xls)"
        )

        if file_path:
            # Salva o diretório para uso futuro
            ConfigManager().set_value('ultimo_diretorio', os.path.dirname(file_path))

            self.set_file(file_path)
            self.fileDropped.emit(file_path, self.report_type)
            self.highlight_success()

    def dragEnterEvent(self, event):
        """Permite a entrada de arquivos arrastados"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

            # Aplicar estilo de destaque na área de drop
            # Usar QPalette para destaque
            palette = self.palette()
            border_color = AppColors.MULTAS if self.report_type == "multas" else AppColors.PENDENCIAS
            palette.setColor(QPalette.ColorRole.Window, AppColors.ACCENT_LIGHT)
            self.setPalette(palette)
            self.setAutoFillBackground(True)

    def dragLeaveEvent(self, event):
        """Remove o estilo de destaque quando o arquivo sai da área"""
        # Restaurar o estilo original usando StyleManager
        StyleManager.configure_drop_area(self, self.report_type)

        # Se um arquivo já estiver selecionado, restaura o visual adequado
        if self.file_path:
            self.set_file(self.file_path)

    def dropEvent(self, event):
        """Processa o arquivo quando solto na área"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith((".xlsx", ".xls")):
                self.set_file(file_path)
                self.fileDropped.emit(file_path, self.report_type)
                self.highlight_success()
            else:
                QMessageBox.warning(self, "Formato Inválido",
                                   "Por favor, arraste um arquivo Excel válido (.xlsx ou .xls).")
                self.highlight_error()
        else:
            # Restaura o estilo se nenhum arquivo for válido
            StyleManager.configure_drop_area(self, self.report_type)

    def highlight_success(self):
        """Adiciona um efeito visual temporário de sucesso"""
        # Aplicar destaque usando QPalette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, AppColors.ACCENT_LIGHT)
        if self.report_type == "multas":
            palette.setColor(QPalette.ColorRole.WindowText, AppColors.MULTAS)
        else:
            palette.setColor(QPalette.ColorRole.WindowText, AppColors.PENDENCIAS)

        # Destacar a borda
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setFrameShadow(QFrame.Shadow.Raised)

        self.setPalette(palette)
        self.highlight_timer.start(800)  # Reseta após 800ms

    def highlight_error(self):
        """Adiciona um efeito visual temporário de erro"""
        # Aplicar destaque usando QPalette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, AppColors.WARNING_LIGHT)
        palette.setColor(QPalette.ColorRole.WindowText, AppColors.WARNING)

        # Destacar a borda
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setFrameShadow(QFrame.Shadow.Raised)

        self.setPalette(palette)
        self.highlight_timer.start(800)  # Reseta após 800ms

    def reset_highlight(self):
        """Restaura o estilo após uma animação"""
        if self.file_path:
            # Restaurar estilo básico
            StyleManager.configure_drop_area(self, self.report_type)

            # Aplicar efeito de "arquivo selecionado"
            palette = self.palette()
            if self.report_type == "multas":
                palette.setColor(QPalette.ColorRole.WindowText, AppColors.MULTAS)
            else:
                palette.setColor(QPalette.ColorRole.WindowText, AppColors.PENDENCIAS)

            self.setPalette(palette)

            # Configurar status label
            StyleManager.configure_status_label(self.status_label, True)
        else:
            # Restaurar completamente o estilo original
            StyleManager.configure_drop_area(self, self.report_type)

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

        # Conectar sinal de mudança de tab para animação
        self.tabs.currentChanged.connect(self.animate_tab_change)

        # Setup das abas
        self.setup_import_tab()
        self.setup_results_tab()
        self.setup_summary_tab()
        self.setup_template_tab()
        self.setup_export_tab()

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

    def animate_tab_change(self, index):
        """Anima a mudança de abas para uma experiência mais suave"""
        # Animar a barra de progresso como feedback visual
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i in range(101):
            QTimer.singleShot(i * 3, lambda v=i: self.progress_bar.setValue(v))

        QTimer.singleShot(350, lambda: self.progress_bar.setVisible(False))

    def setup_import_tab(self):
        """Configura a aba de importação de arquivos"""
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        import_layout.setContentsMargins(20, 20, 20, 20)
        import_layout.setSpacing(15)

        # Container para o cabeçalho da aba
        header_container = QWidget()
        header_container.setObjectName("tabHeader")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 20)

        # Cabeçalho com título e descrição
        header = QLabel("Importação de Relatórios")
        StyleManager.configure_header_label(header)
        header_layout.addWidget(header)

        description = QLabel(
            "Arraste e solte os arquivos Excel dos relatórios 86 (Multas) e 76 (Pendências) "
            "ou clique nas áreas abaixo para selecionar os arquivos."
        )
        StyleManager.configure_subheader_label(description)
        header_layout.addWidget(description)

        import_layout.addWidget(header_container)

        # Card de instruções
        instructions_card = QFrame()
        instructions_card.setObjectName("instructionsCard")
        instructions_layout = QVBoxLayout(instructions_card)

        instructions_title = QLabel("Como funciona:")
        font = instructions_title.font()
        font.setPointSize(14)
        font.setBold(True)
        instructions_title.setFont(font)

        # Configurar cor usando QPalette
        palette = instructions_title.palette()
        palette.setColor(QPalette.ColorRole.WindowText, AppColors.INFO)
        instructions_title.setPalette(palette)

        instructions_layout.addWidget(instructions_title)

        instructions_text = QLabel(
            "1. Selecione os dois relatórios das áreas abaixo\n"
            "2. Os relatórios serão validados automaticamente\n"
            "3. Clique em \"Unificar Relatórios\" para processar os dados\n"
            "4. Navegue pelas abas para visualizar resultados e exportar dados"
        )

        # Configurar o texto de instruções com QPalette
        palette = instructions_text.palette()
        palette.setColor(QPalette.ColorRole.WindowText, AppColors.TEXT)
        instructions_text.setPalette(palette)
        instructions_layout.addWidget(instructions_text)

        import_layout.addWidget(instructions_card)

        # Opção para verificar data dos arquivos
        date_check_container = QFrame()
        date_check_container.setObjectName("dateCheckCard")
        StyleManager.configure_date_check_container(date_check_container)
        date_check_layout = QHBoxLayout(date_check_container)

        date_info_label = QLabel("Verificação de data:")
        font = date_info_label.font()
        font.setBold(True)
        date_info_label.setFont(font)
        date_check_layout.addWidget(date_info_label)

        self.check_date = QPushButton("Verificar se os arquivos são do dia atual")
        self.check_date.setObjectName("checkDateButton")
        self.check_date.setCheckable(True)
        self.check_date.setChecked(True)

        # Configurar cores usando AppColors e QPalette
        self.update_check_date_button()

        self.check_date.clicked.connect(self.toggle_date_check)
        date_check_layout.addWidget(self.check_date)
        date_check_layout.addStretch()

        import_layout.addWidget(date_check_container)

        # Container para as áreas de drop
        drop_container = QWidget()
        drop_layout = QHBoxLayout(drop_container)
        drop_layout.setSpacing(20)

        # Área de drop para relatório de multas (86)
        self.multas_drop_area = FileDropArea(report_type="multas")
        self.multas_drop_area.fileDropped.connect(self.handle_file_dropped)
        drop_layout.addWidget(self.multas_drop_area)

        # Área de drop para relatório de pendências (76)
        self.pendencias_drop_area = FileDropArea(report_type="pendencias")
        self.pendencias_drop_area.fileDropped.connect(self.handle_file_dropped)
        drop_layout.addWidget(self.pendencias_drop_area)

        # Adicionar container ao layout principal
        import_layout.addWidget(drop_container, 1)

        # Container para botão de unificação e progresso
        action_container = QFrame()
        action_container.setObjectName("actionContainer")
        action_container.setStyleSheet(ACTION_CONTAINER_STYLE)
        action_layout = QVBoxLayout(action_container)

        # Botão para unificar relatórios
        unify_container = QWidget()
        unify_layout = QHBoxLayout(unify_container)
        unify_layout.setContentsMargins(0, 0, 0, 0)
        unify_layout.addStretch()

        # Criação do botão com ícone
        self.unify_button = QPushButton("  Unificar Relatórios  ")
        self.unify_button.setObjectName("unifyButton")

        # Adicionar ícone usando QIcon
        icon_size = QSize(24, 24)
        # Usamos símbolos Unicode para compatibilidade com diferentes plataformas
        self.unify_button.setIcon(QIcon.fromTheme("document-save", QIcon()))
        self.unify_button.setIconSize(icon_size)

        # Configurar tamanho do botão
        self.unify_button.setMinimumWidth(250)
        self.unify_button.setMinimumHeight(50)

        # Configurar fonte manualmente para precisão
        font = QFont("Segoe UI", 12)
        font.setBold(True)
        self.unify_button.setFont(font)

        # Usar StyleManager para configurações básicas
        StyleManager.configure_button(self.unify_button, 'primary')

        # Garantir que o texto e ícone sejam visíveis (solução de contingência)
        self.unify_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #2196F3;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #90CAF9;
                color: rgba(255, 255, 255, 150);
            }
        """)

        # Desativar o botão por padrão até que os arquivos sejam carregados
        self.unify_button.setEnabled(False)

        # Conectar ação
        self.unify_button.clicked.connect(self.unify_reports)

        unify_layout.addWidget(self.unify_button)
        unify_layout.addStretch()

        action_layout.addWidget(unify_container)

        # Barra de progresso (inicialmente oculta)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("progressBar")

        # Configurar a barra de progresso com StyleManager
        StyleManager.configure_progress_bar(self.progress_bar)

        action_layout.addWidget(self.progress_bar)

        import_layout.addWidget(action_container)

        # Adicionar a aba ao widget de abas
        self.tabs.addTab(import_tab, "📥 Importação")

    def setup_results_tab(self):
        """Configura a aba de resultados"""
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        results_layout.setContentsMargins(20, 20, 20, 20)
        results_layout.setSpacing(15)

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

        results_layout.addWidget(title_container)

        # Área de resultados em um container estilizado
        result_container = QFrame()
        result_container.setObjectName("resultContainer")
        result_layout = QVBoxLayout(result_container)

        self.result_area = QTextBrowser()
        self.result_area.setOpenExternalLinks(True)  # Permite abrir links
        result_layout.addWidget(self.result_area)

        results_layout.addWidget(result_container)

        # Aplicar estilos nativos
        StyleManager.configure_frame(result_container, 'card')
        StyleManager.configure_text_edit(self.result_area)

        # Adicionar a aba ao widget principal
        self.tabs.addTab(results_tab, "📊 Resultados")

    def setup_summary_tab(self):
        """Configura a aba de resumo"""
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        summary_layout.setSpacing(15)

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

        summary_layout.addWidget(header_container)

        # Área de resumo em container estilizado
        summary_container = QFrame()
        summary_container.setObjectName("summaryContainer")
        summary_container_layout = QVBoxLayout(summary_container)

        self.summary_label = QTextBrowser()
        summary_container_layout.addWidget(self.summary_label)

        summary_layout.addWidget(summary_container)

        # Aplicar estilos nativos
        StyleManager.configure_frame(summary_container, 'card')
        StyleManager.configure_text_edit(self.summary_label)

        # Adicionar a aba ao widget principal
        self.tabs.addTab(summary_tab, "📋 Resumo")

    def setup_template_tab(self):
        """Configura a aba de templates de email"""
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)
        template_layout.setContentsMargins(20, 20, 20, 20)
        template_layout.setSpacing(15)

        # Título e subtítulo
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 10)

        # Adicionar cabeçalho
        header = QLabel("Templates de Email")
        StyleManager.configure_header_label(header)
        header_layout.addWidget(header)

        # Adicionar descrição
        description = QLabel("Selecione o tipo de notificação e personalize o template para comunicação com os usuários")
        StyleManager.configure_subheader_label(description)
        header_layout.addWidget(description)

        template_layout.addWidget(header_container)

        # Container para os controles em um card
        controls_container = QFrame()
        controls_container.setObjectName("templateControlsCard")
        StyleManager.configure_frame(controls_container, 'card')
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setSpacing(20)

        # Grupo de radio buttons para os tipos de template
        radio_group = QGroupBox("Tipo de Notificação")
        radio_group.setObjectName("radioGroupCard")
        StyleManager.configure_radio_group(radio_group)
        radio_layout = QVBoxLayout(radio_group)
        radio_layout.setSpacing(10)

        # Criar os radio buttons com ícones e texto mais descritivo
        self.rb_apenas_multa = QRadioButton(" Apenas Multa")
        self.rb_apenas_multa.setObjectName("rb1")
        StyleManager.configure_radio_button(self.rb_apenas_multa, 'warning')
        self.rb_apenas_multa.setChecked(True)  # Selecionado por padrão

        self.rb_apenas_pendencia = QRadioButton(" Apenas Pendência")
        self.rb_apenas_pendencia.setObjectName("rb2")
        StyleManager.configure_radio_button(self.rb_apenas_pendencia, 'info')

        self.rb_multa_e_pendencia = QRadioButton(" Multa e Pendência")
        self.rb_multa_e_pendencia.setObjectName("rb3")
        StyleManager.configure_radio_button(self.rb_multa_e_pendencia, 'accent')

        # Adicionar os radio buttons ao grupo
        radio_layout.addWidget(self.rb_apenas_multa)
        radio_layout.addWidget(self.rb_apenas_pendencia)
        radio_layout.addWidget(self.rb_multa_e_pendencia)

        # Adicionar espaçamento e preenchimento no final
        radio_layout.addStretch()

        # Configurar a largura máxima do grupo
        radio_group.setMinimumWidth(200)
        radio_group.setMaximumWidth(250)

        # Adicionar o grupo ao layout de controles
        controls_layout.addWidget(radio_group)

        # Container para os botões com layout vertical
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(10)

        # Título para os botões
        button_title = QLabel("Ações")
        button_title.setStyleSheet("font-weight: bold; color: #3f51b5; font-size: 14px;")
        button_layout.addWidget(button_title)

        # Espaçamento
        button_layout.addSpacing(5)

        # Botão para copiar template
        self.copy_button = QPushButton("Copiar Template")
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setIcon(QIcon().fromTheme("edit-copy"))
        StyleManager.configure_button(self.copy_button, 'info')
        self.copy_button.clicked.connect(self.copy_template)
        button_layout.addWidget(self.copy_button)

        # Botão para editar template
        self.edit_button = QPushButton("Editar Template")
        self.edit_button.setObjectName("editButton")
        self.edit_button.setIcon(QIcon().fromTheme("document-edit"))
        StyleManager.configure_button(self.edit_button, 'secondary')
        self.edit_button.clicked.connect(self.edit_template)
        button_layout.addWidget(self.edit_button)

        # Adicionar espaçamento no final
        button_layout.addStretch()

        # Adicionar o container do botão ao layout de controles
        controls_layout.addWidget(button_container)

        # Adicionar espaçamento à direita
        controls_layout.addStretch()

        # Adicionar o container de controles ao layout principal
        template_layout.addWidget(controls_container)

        # Container da área de exibição do template
        template_view_container = QFrame()
        template_view_container.setObjectName("templateViewCard")
        StyleManager.configure_frame(template_view_container, 'card')
        template_view_layout = QVBoxLayout(template_view_container)

        # Área de exibição do template
        self.template_area = QTextBrowser()
        self.template_area.setOpenExternalLinks(True)  # Permitir abrir links
        self.template_area.setStyleSheet("""
            QTextBrowser {
                border: none;
                background-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                selection-background-color: #e3f2fd;
                selection-color: #2196f3;
            }
        """)
        template_view_layout.addWidget(self.template_area)

        # Adicionar o container da área de template ao layout principal
        template_layout.addWidget(template_view_container, 1)  # 1 para expandir

        # Conectar eventos dos radio buttons
        self.rb_apenas_multa.toggled.connect(lambda: self.update_template(self.rb_apenas_multa) if self.rb_apenas_multa.isChecked() else None)
        self.rb_apenas_pendencia.toggled.connect(lambda: self.update_template(self.rb_apenas_pendencia) if self.rb_apenas_pendencia.isChecked() else None)
        self.rb_multa_e_pendencia.toggled.connect(lambda: self.update_template(self.rb_multa_e_pendencia) if self.rb_multa_e_pendencia.isChecked() else None)

        # Exibir o template inicial
        self.show_template_apenas_multa()

        # Adicionar a aba ao widget principal
        self.tabs.addTab(template_tab, "✉️ Templates")

    def setup_export_tab(self):
        """Configura a aba de exportação"""
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.setContentsMargins(20, 20, 20, 20)
        export_layout.setSpacing(20)

        # Seção de exportação
        export_section = QGroupBox("Exportar Dados")
        export_section_layout = QVBoxLayout(export_section)

        # Botões de exportação
        export_buttons_layout = QHBoxLayout()

        # Botão de exportação JSON
        self.export_button = QPushButton("  Exportar para JSON  ")
        self.export_button.setObjectName("exportJsonButton")
        self.export_button.setIcon(QIcon.fromTheme("text-x-script", QIcon()))
        self.export_button.setIconSize(QSize(24, 24))
        self.export_button.setMinimumWidth(250)
        self.export_button.setMinimumHeight(50)
        font = QFont("Segoe UI", 12)
        font.setBold(True)
        self.export_button.setFont(font)

        # Estilo básico
        StyleManager.configure_button(self.export_button, 'success')

        # Inicialmente desabilitado
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_json)
        export_buttons_layout.addWidget(self.export_button)

        # Botões para outros formatos
        export_excel_button = self.create_export_button("Exportar para Excel", icon_name="x-office-spreadsheet", export_func=self.export_excel)
        export_buttons_layout.addWidget(export_excel_button)

        export_csv_button = self.create_export_button("Exportar para CSV", icon_name="text-csv", export_func=self.export_csv)
        export_buttons_layout.addWidget(export_csv_button)

        export_pdf_button = self.create_export_button("Exportar para PDF", icon_name="application-pdf", export_func=self.export_pdf)
        export_buttons_layout.addWidget(export_pdf_button)

        # Adicionar o layout de botões ao layout da seção
        export_section_layout.addLayout(export_buttons_layout)

        # Adicionar a seção ao layout principal da tab
        export_layout.addWidget(export_section)

        # Adicionar espaçamento final
        export_layout.addStretch()

        # Adicionar a aba ao widget principal
        self.tabs.addTab(export_tab, "📤 Exportação")

    def export_excel(self):
        """Exporta os dados unificados para um arquivo Excel"""
        if self.unified_data is None:
            self.show_message("Erro", "Não há dados unificados para exportar.", QMessageBox.Icon.Warning)
            return

        try:
            # Perguntar onde salvar o arquivo
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar arquivo Excel", "", "Excel Files (*.xlsx)")

            if output_path:
                # Animar progresso para feedback visual
                self.animate_progress()

                # Exportar para Excel (implementação simplificada)
                self.unified_data.to_excel(output_path, index=False)

                # Mostrar mensagem de sucesso
                self.show_message("Sucesso", f"Arquivo Excel gerado com sucesso: {output_path}")

        except Exception as e:
            self.show_message("Erro", f"Erro ao exportar para Excel: {str(e)}", QMessageBox.Icon.Critical)

    def export_csv(self):
        """Exporta os dados unificados para um arquivo CSV"""
        if self.unified_data is None:
            self.show_message("Erro", "Não há dados unificados para exportar.", QMessageBox.Icon.Warning)
            return

        try:
            # Perguntar onde salvar o arquivo
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar arquivo CSV", "", "CSV Files (*.csv)")

            if output_path:
                # Animar progresso para feedback visual
                self.animate_progress()

                # Exportar para CSV (implementação simplificada)
                self.unified_data.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')

                # Mostrar mensagem de sucesso
                self.show_message("Sucesso", f"Arquivo CSV gerado com sucesso: {output_path}")

        except Exception as e:
            self.show_message("Erro", f"Erro ao exportar para CSV: {str(e)}", QMessageBox.Icon.Critical)

    def export_pdf(self):
        """Exporta os dados unificados para um arquivo PDF"""
        if self.unified_data is None:
            self.show_message("Erro", "Não há dados unificados para exportar.", QMessageBox.Icon.Warning)
            return

        try:
            # Perguntar onde salvar o arquivo
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar arquivo PDF", "", "PDF Files (*.pdf)")

            if output_path:
                # Animar progresso para feedback visual
                self.animate_progress()

                # Aqui seria implementada a exportação para PDF
                # Como é apenas uma demonstração, vamos simular a exportação
                with open(output_path, 'w') as f:
                    f.write("Simulação de exportação PDF")

                # Mostrar mensagem de sucesso
                self.show_message("Sucesso", f"Arquivo PDF gerado com sucesso: {output_path}")

        except Exception as e:
            self.show_message("Erro", f"Erro ao exportar para PDF: {str(e)}", QMessageBox.Icon.Critical)

    def handle_file_dropped(self, file_path, file_type):
        """Manipula quando um arquivo é solto ou selecionado em uma área de drop"""
        try:
            # Verificar data do arquivo
            df = read_excel_file(file_path, verificar_data=self.verificar_data)
            df = clean_column_names(df)

            # Atribuir ao tipo correto
            if file_type == "multas":
                self.multas_file = file_path
                self.multas_df = df
                self.animate_progress()
            else:
                self.pendencias_file = file_path
                self.pendencias_df = df
                self.animate_progress()

            # Atualizar resumo
            self.update_summary()

            # Habilitar botão de unificação se ambos os arquivos estiverem carregados
            should_enable = bool(self.multas_file and self.pendencias_file)
            self.unify_button.setEnabled(should_enable)

            # Se ambos os arquivos estiverem carregados, adicionar efeito de pulso ao botão
            if should_enable:
                self.start_button_pulse_effect(self.unify_button)

        except ValueError as e:
            if "não é do dia atual" in str(e):
                error_summary = (
                    f"⚠️ Erro de Data no relatório de {file_type.capitalize()}: {str(e)}\n"
                    "Desmarque a opção 'Verificar se os arquivos são do dia atual' para processar este arquivo."
                )
                self.show_message("Erro de Data", error_summary, QMessageBox.Icon.Warning)

                # Remover referência ao arquivo com erro
                if file_type == "multas":
                    self.multas_file = None
                    self.multas_drop_area.set_file(None)
                else:
                    self.pendencias_file = None
                    self.pendencias_drop_area.set_file(None)
            else:
                self._handle_generic_error(e)
        except Exception as e:
            self._handle_generic_error(e)

    def start_button_pulse_effect(self, button):
        """Inicia o efeito de pulso para o botão especificado"""
        if not hasattr(self, 'pulse_timers'):
            self.pulse_timers = {}

        if button in self.pulse_timers:
            self.pulse_timers[button].stop()

        timer = QTimer(self)
        self.pulse_timers[button] = timer

        # Configura variáveis para controlar o pulso
        button.pulse_intensity = 0
        button.pulse_direction = 1  # 1 para aumentar, -1 para diminuir

        # Conecta o timer ao método de pulso
        timer.timeout.connect(lambda: self.pulse_button(button))
        timer.start(40)  # Atualiza a cada 40ms para animação suave

    def stop_button_pulse_effect(self, button):
        """Para o efeito de pulso para o botão especificado"""
        if hasattr(self, 'pulse_timers') and button in self.pulse_timers:
            self.pulse_timers[button].stop()
            # Redefine o efeito do botão com a configuração normal
            if button.objectName() == "unifyButton":
                StyleManager.configure_button(button, 'primary')
            elif button.objectName() == "exportJsonButton":
                StyleManager.configure_button(button, 'success')

            # Reconfigura o efeito de sombra - removido devido a incompatibilidade
            # com QGraphicsDropShadowEffect

    def pulse_button(self, button):
        """Aplica o efeito de pulso ao botão"""
        # Aumenta ou diminui a intensidade
        button.pulse_intensity += button.pulse_direction * 5

        # Inverte a direção quando atinge os limites
        if button.pulse_intensity >= 100:
            button.pulse_direction = -1
        elif button.pulse_intensity <= 0:
            button.pulse_direction = 1

        # Calcula a cor com base na intensidade
        if button.objectName() == "unifyButton":
            base_color = AppColors.PRIMARY
        elif button.objectName() == "exportJsonButton":
            base_color = AppColors.SUCCESS
        else:
            return

        # Calcula a cor do pulso (mais clara)
        h, s, v, a = base_color.getHsv()
        pulse_factor = button.pulse_intensity / 100 * 30  # Aumenta o brilho em até 30%
        v = int(min(255, v + pulse_factor))  # Convertendo para inteiro
        pulse_color = QColor.fromHsv(h, s, v, a)

        # Aplica a cor ao botão
        palette = button.palette()
        palette.setColor(QPalette.ColorRole.Button, pulse_color)
        button.setPalette(palette)

        # Ajuste de sombra removido devido a incompatibilidade com QGraphicsDropShadowEffect

    def unify_reports(self):
        """Unifica os dois relatórios em um único DataFrame"""
        # Parar o efeito de pulso quando o botão for clicado
        self.stop_button_pulse_effect(self.unify_button)

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
            self.update_summary()

            # Exibir os resultados no dashboard
            self.display_unified_results()

            # Mostrar template padrão (Apenas Multa)
            self.update_template(None)

            # Habilitar o botão de exportação
            self.export_button.setEnabled(True)

            self.show_message("Sucesso", "Relatórios unificados com sucesso!")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erro detalhado: {error_details}")
            self.show_message("Erro", f"Erro ao unificar relatórios: {str(e)}", QMessageBox.Icon.Critical)

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
                        <div style='border-left: 4px solid #3498db; padding-left: 10px; margin-bottom: 15px;'>
                            <p style='color: #555; font-style: italic;'>Informações sobre multas de usuários da biblioteca.</p>
                        </div>

                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                            <h4 style='margin-top: 0; color: #3498db;'>Resumo</h4>
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
                        <div style='border-left: 4px solid #e74c3c; padding-left: 10px; margin-bottom: 15px;'>
                            <p style='color: #555; font-style: italic;'>Informações sobre itens pendentes de devolução.</p>
                        </div>

                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                            <h4 style='margin-top: 0; color: #e74c3c;'>Resumo</h4>
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
                        <div style='border-left: 4px solid #27ae60; padding-left: 10px; margin-bottom: 15px;'>
                            <p style='color: #555; font-style: italic;'>Pessoas cadastradas sem email para contato direto.</p>
                        </div>

                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                            <h4 style='margin-top: 0; color: #27ae60;'>Resumo</h4>
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
                        <div style='border-left: 4px solid #f39c12; padding-left: 10px; margin-bottom: 15px;'>
                            <p style='color: #555; font-style: italic;'>Informações sobre empréstimos de chaves ativos.</p>
                        </div>

                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
                            <h4 style='margin-top: 0; color: #f39c12;'>Resumo</h4>
                            <ul style='list-style-type: none; padding-left: 0;'>
                                <li><strong>Total de chaves emprestadas:</strong> {total_chaves}</li>
                                <li><strong>Pessoas com chaves:</strong> {unique_users_chaves}</li>
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

    def display_categories(self):
        """
        Exibe as categorias de usuários na interface conforme solicitado.
        """
        if self.unified_data is None:
            return

        # Obter categorias
        categories = categorize_users(self.unified_data)

        # Criar estrutura para dados de dias de atraso
        dias_atraso_rows = ""
        if categories['rel76']['pessoas_por_dias_atraso']:
            for pessoa in categories['rel76']['pessoas_por_dias_atraso']:
                dias_atraso_rows += f"""
                    <tr style='border-bottom: 1px solid #eee;'>
                        <td style='padding: 5px;'>{pessoa[0]}</td>
                        <td style='padding: 5px;'>{pessoa[1]}</td>
                        <td style='padding: 5px; text-align: center;'>{pessoa[2]}</td>
                    </tr>
                """

        # Criar estrutura para dados de pessoas sem email
        pessoas_sem_email_rows = ""
        for matricula, nome in categories['sem_email']['pessoas']:
            pessoas_sem_email_rows += f"""
                <tr style='border-bottom: 1px solid #eee;'>
                    <td style='padding: 5px;'>{matricula}</td>
                    <td style='padding: 5px;'>{nome}</td>
                </tr>
            """

        # Ajustar para usar o novo método do StyleManager
        if hasattr(self, 'template_area') and self.template_area is not None:
            StyleManager.configure_categories_text_browser(self.template_area, categories)

    def export_json(self):
        """Exporta os dados unificados para um arquivo JSON"""
        if self.unified_data is None:
            self.show_message("Erro", "Não há dados unificados para exportar.", QMessageBox.Icon.Warning)
            return

        try:
            # Perguntar onde salvar o arquivo
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Salvar arquivo JSON", "", "JSON Files (*.json)")

            if output_path:
                from modules.data_processor import generate_json_file

                # Animar progresso para feedback visual
                self.animate_progress()

                # Exportar para JSON usando a função existente
                json_path = generate_json_file(self.unified_data, output_path)

                # Mostrar mensagem de sucesso
                self.show_message("Sucesso", f"Arquivo JSON gerado com sucesso: {json_path}")

        except Exception as e:
            self.show_message("Erro", f"Erro ao exportar para JSON: {str(e)}", QMessageBox.Icon.Critical)

    def update_check_date_button(self):
        """Atualiza o estilo do botão de verificação de data usando QPalette"""
        # Configurar o botão com cores baseadas em seu estado
        palette = self.check_date.palette()

        if self.check_date.isChecked():
            # Botão ativado - usar cor de ACCENT (verde)
            palette.setColor(QPalette.ColorRole.Button, AppColors.ACCENT)
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        else:
            # Botão desativado - usar cor de WARNING (vermelho)
            palette.setColor(QPalette.ColorRole.Button, AppColors.WARNING)
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)

        self.check_date.setPalette(palette)
        self.check_date.setAutoFillBackground(True)

        # Ajustar o estilo do botão
        font = self.check_date.font()
        font.setBold(True)
        self.check_date.setFont(font)

        # Definir padding e bordas arredondadas
        self.check_date.setContentsMargins(8, 8, 8, 8)

    def toggle_date_check(self, checked):
        """Alterna a verificação de data dos arquivos"""
        self.verificar_data = checked

        # Atualizar o estilo do botão
        self.update_check_date_button()

        # Atualizar o texto do botão
        if checked:
            self.check_date.setText("Verificar se os arquivos são do dia atual")
        else:
            self.check_date.setText("Ignorar a data dos arquivos")

    def animate_progress(self):
        """Anima a barra de progresso para feedback visual"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i in range(101):
            QTimer.singleShot(i * 10, lambda v=i: self.progress_bar.setValue(v))

        QTimer.singleShot(1100, lambda: self.progress_bar.setVisible(False))

    def _handle_generic_error(self, e):
        """Método auxiliar para tratar erros genéricos"""
        self.show_message("Erro", f"Erro no processamento: {str(e)}", QMessageBox.Icon.Critical)

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
            if hasattr(self, 'result_area') and self.result_area is not None:
                StyleManager.configure_welcome_text_browser(self.result_area)
            elif hasattr(self, 'template_area') and self.template_area is not None:
                StyleManager.configure_welcome_text_browser(self.template_area)
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

        # Configurar botões principais
        if hasattr(self, 'unify_button'):
            StyleManager.configure_button(self.unify_button, 'primary')

        if hasattr(self, 'export_button'):
            StyleManager.configure_button(self.export_button, 'success')

        if hasattr(self, 'check_date'):
            self.update_check_date_button()

        if hasattr(self, 'copy_button'):
            StyleManager.configure_button(self.copy_button, 'info')

        if hasattr(self, 'edit_button'):
            StyleManager.configure_button(self.edit_button, 'secondary')

        # Configurar áreas de texto
        if hasattr(self, 'template_area'):
            StyleManager.configure_text_edit(self.template_area)

        if hasattr(self, 'result_area'):
            StyleManager.configure_text_edit(self.result_area)

        if hasattr(self, 'summary_label'):
            StyleManager.configure_text_edit(self.summary_label)

        # Configurar barra de progresso
        if hasattr(self, 'progress_bar'):
            StyleManager.configure_progress_bar(self.progress_bar)

        # Configurar áreas de drop de arquivos
        if hasattr(self, 'multas_drop_area'):
            StyleManager.configure_drop_area(self.multas_drop_area, "multas")

        if hasattr(self, 'pendencias_drop_area'):
            StyleManager.configure_drop_area(self.pendencias_drop_area, "pendencias")

        # Configurar frames de informação
        frames_info = [f for f in dir(self) if isinstance(getattr(self, f, None), QFrame)]
        for frame_name in frames_info:
            frame = getattr(self, frame_name)
            if frame.objectName() == "instructionsCard":
                StyleManager.configure_frame(frame, 'info')
            elif frame.objectName() == "exportInfoCard":
                StyleManager.configure_frame(frame, 'success')
            elif frame.objectName() in ["resultContainer", "summaryContainer", "templateViewCard"]:
                StyleManager.configure_frame(frame, 'card')

    def update_template(self, button):
        """Atualiza o template conforme a seleção do usuário"""
        if self.rb_apenas_multa.isChecked():
            self.show_template_apenas_multa()
        elif self.rb_apenas_pendencia.isChecked():
            self.show_template_apenas_pendencia()
        elif self.rb_multa_e_pendencia.isChecked():
            self.show_template_multa_e_pendencia()

    def show_template_apenas_multa(self):
        """Exibe o template para usuários com apenas multa"""
        # Tentar carregar do config manager primeiro
        saved_template = self.config_manager.get_value('template_apenas_multa')
        if saved_template:
            self.template_area.setHtml(saved_template)
            return

        # Template padrão se não tiver nenhum salvo - usando AppColors
        template = f"""
        <div style='font-family: Arial, sans-serif; color: {AppColors.TEXT.name()}; line-height: 1.6;'>
            <h3 style='color: {AppColors.INFO.name()};'>Template: Notificação de Multa</h3>
            <hr style='border: 1px solid {AppColors.BORDER.name()};'>
            <pre style='background-color: {AppColors.BACKGROUND.name()}; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: Consolas, monospace;'>
Prezado(a) {{formtext: name=nome; trim=yes; formatter=(value) -> upper(value)}},

Conforme estabelecido no [Regulamento Interno das Bibliotecas do Instituto Federal Catarinense](https://biblioteca.ifc.edu.br/wp-content/uploads/sites/53/2023/04/SIBI-Regulamento.pdf), artigo 44, é nossa responsabilidade notificá-lo(a) sobre as pendências em sua conta de usuário na biblioteca.

Constata-se a existência de multa acumulada no valor total de R$ {{formtext: name=valor; default=00,00}}. referente ao(s) seguinte(s) item(ns):

- {{formtext: name=Obra}}
    - Data de Empréstimo: {{formdate: DD/MM/YYYY; name=emprestimo}}
    - Data de Devolução Prevista: {{formdate: DD/MM/YYYY; name=prevista}}
    - Data de Devolução Efetiva: {{formdate: DD/MM/YYYY; name=efetiva}}
    - Dias de Atraso: {{=datetimediff(datetimeparse(prevista, "DD/MM/YYYY"), datetimeparse(efetiva, "DD/MM/YYYY"), "D")}}

Salientamos que, para renovar ou realizar novos empréstimos, as multas devem estar abaixo de R$ 10,00. No entanto, para emitir a Declaração de Nada Consta, é necessário que todas as multas e pendências na biblioteca sejam totalmente quitadas.

Em caso de perda do material emprestado, deverá ser informado e proceder com a reposição do mesmo.

Regularize sua situação com a biblioteca o mais breve possível, para juntos, mantermos funcionando de forma eficiente e acessível para toda a comunidade acadêmica.

Estamos à disposição para esclarecer dúvidas, ou para mais informações.

Atenciosamente,
            </pre>
        </div>
        """
        self.template_area.setHtml(template)
        # Salvar o template padrão na configuração
        self.config_manager.set_value('template_apenas_multa', template)

    def show_template_apenas_pendencia(self):
        """Exibe o template para usuários apenas com pendências"""
        # Tentar carregar do config manager primeiro
        saved_template = self.config_manager.get_value('template_apenas_pendencia')
        if saved_template:
            self.template_area.setHtml(saved_template)
            return

        # Template padrão se não tiver nenhum salvo
        template = """
        <div style='font-family: Arial, sans-serif; color: #333; line-height: 1.6;'>
            <h3 style='color: #e74c3c;'>Template: Notificação de Pendência</h3>
            <hr style='border: 1px solid #eee;'>
            <pre style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: Consolas, monospace;'>
Prezado(a) {formtext: name=nome; trim=yes; formatter=(value) -> upper(value)},

Conforme estabelecido no [Regulamento Interno das Bibliotecas do Instituto Federal Catarinense](https://biblioteca.ifc.edu.br/wp-content/uploads/sites/53/2023/04/SIBI-Regulamento.pdf), artigo 44, é nossa responsabilidade notificá-lo(a) sobre as pendências em sua conta de usuário na biblioteca.

De acordo com os registros em nosso sistema, observamos que você possui o(s) seguinte(s) item(ns) em atraso:

- {formtext: name=Obra1}
    - Data de Empréstimo: {formdate: DD/MM/YYYY; name=emprestimo1}
    - Data de Devolução Prevista: {formdate: DD/MM/YYYY; name=prevista1}
    - Dias de Atraso: {=datetimediff(datetimeparse(prevista1, "DD/MM/YYYY"), today(), "D")}

Conforme o artigo 44, Inciso I, do Regulamento, informamos que a multa aplicada é de R$ 1,00 (um real) por dia útil de atraso para cada material emprestado.

Salientamos que, para renovar ou realizar novos empréstimos, as multas devem estar abaixo de R$ 10,00. No entanto, para emitir a Declaração de Nada Consta, é necessário que todas as multas e pendências na biblioteca sejam totalmente quitadas.

Em caso de perda do material emprestado, deverá ser informado e proceder com a reposição do mesmo.

Regularize sua situação com a biblioteca o mais breve possível, para juntos, mantermos funcionando de forma eficiente e acessível para toda a comunidade acadêmica.

Estamos à disposição para esclarecer dúvidas, ou para mais informações.

Agradecemos sua atenção e colaboração.

Atenciosamente,
            </pre>
        </div>
        """
        self.template_area.setHtml(template)
        # Salvar o template padrão na configuração
        self.config_manager.set_value('template_apenas_pendencia', template)

    def show_template_multa_e_pendencia(self):
        """Exibe o template para usuários com multas e pendências"""
        # Tentar carregar do config manager primeiro
        saved_template = self.config_manager.get_value('template_multa_e_pendencia')
        if saved_template:
            self.template_area.setHtml(saved_template)
            return

        # Template padrão se não tiver nenhum salvo
        template = """
        <div style='font-family: Arial, sans-serif; color: #333; line-height: 1.6;'>
            <h3 style='color: #f39c12;'>Template: Notificação de Multa e Pendência</h3>
            <hr style='border: 1px solid #eee;'>
            <pre style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: Consolas, monospace;'>
Prezado(a) {formtext: name=nome; trim=yes; formatter=(value) -> upper(value)},

Conforme estabelecido no Regulamento Interno das Bibliotecas do Instituto Federal Catarinense, artigo 44, é nossa responsabilidade notificá-lo(a) sobre as pendências em sua conta de usuário na biblioteca.

De acordo com os registros em nosso sistema, observamos que você possui o(s) seguinte(s) item(ns) em atraso:

- {formtext: name=Obra1}
    - Data de Empréstimo: {formdate: DD/MM/YYYY; name=emprestimo1}
    - Data de Devolução Prevista: {formdate: DD/MM/YYYY; name=prevista1}
    - Dias de Atraso: {=datetimediff(datetimeparse(prevista1, "DD/MM/YYYY"), today(), "D")}

Conforme o artigo 44, Inciso I, do Regulamento, informamos que a multa aplicada é de R$ 1,00 (um real) por dia útil de atraso para cada material emprestado.

Constata-se também a existência de multa acumulada no valor total de R$ {formtext: name=valor; default=00,00} referente ao(s) seguinte(s) item(ns):

- {formtext: name=Obra2}
    - Data de Empréstimo: {formdate: DD/MM/YYYY; name=emprestimo2}
    - Data de Devolução Prevista: {formdate: DD/MM/YYYY; name=prevista2}
    - Data de Devolução Efetiva: {formdate: DD/MM/YYYY; name=efetiva2}
    - Dias de Atraso: {=datetimediff(datetimeparse(prevista2, "DD/MM/YYYY"), datetimeparse(efetiva2, "DD/MM/YYYY"), "D")}

Salientamos que, para renovar ou realizar novos empréstimos, as multas devem estar abaixo de R$ 10,00. No entanto, para emitir a Declaração de Nada Consta, é necessário que todas as multas e pendências na biblioteca sejam totalmente quitadas.

Em caso de perda do material emprestado, deverá ser informado e proceder com a reposição do mesmo.

Regularize sua situação com a biblioteca o mais breve possível, para juntos, mantermos funcionando de forma eficiente e acessível para toda a comunidade acadêmica.

Estamos à disposição para esclarecer dúvidas, ou para mais informações.

Agradecemos sua atenção e colaboração.

Atenciosamente,
            </pre>
        </div>
        """
        self.template_area.setHtml(template)
        # Salvar o template padrão na configuração
        self.config_manager.set_value('template_multa_e_pendencia', template)

    def copy_template(self):
        """Copia o template atual para a área de transferência"""
        # Obter o texto puro (sem formatação HTML)
        text = self.template_area.toPlainText()

        # Criar área de transferência
        clipboard = QApplication.clipboard()

        # Definir o texto na área de transferência
        clipboard.setText(text)

        # Feedback para o usuário
        self.show_message("Copiado", "Template copiado para a área de transferência!", QMessageBox.Icon.Information)

    def edit_template(self):
        """Permite ao usuário editar o template atual em uma caixa de diálogo"""
        # Obter o conteúdo atual do template
        current_template = self.template_area.toHtml()

        # Criar um diálogo para edição
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Template")
        dialog.resize(800, 600)

        # Layout principal
        layout = QVBoxLayout(dialog)

        # Criar editor de texto
        editor = QTextEdit()
        editor.setHtml(current_template)
        layout.addWidget(editor)

        # Botões de controle
        buttons = QHBoxLayout()
        save_button = QPushButton("Salvar")
        cancel_button = QPushButton("Cancelar")

        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        # Conectar sinais
        save_button.clicked.connect(lambda: self.save_template_edit(editor.toHtml(), dialog))
        cancel_button.clicked.connect(dialog.reject)

        # Exibir diálogo
        dialog.exec()

    def save_template_edit(self, html_content, dialog):
        """Salva o template editado"""
        self.template_area.setHtml(html_content)

        # Atualizar o template conforme o tipo selecionado
        if self.rb_apenas_multa.isChecked():
            self.config_manager.set_value('template_apenas_multa', html_content)
        elif self.rb_apenas_pendencia.isChecked():
            self.config_manager.set_value('template_apenas_pendencia', html_content)
        elif self.rb_multa_e_pendencia.isChecked():
            self.config_manager.set_value('template_multa_e_pendencia', html_content)

        self.show_message("Template Salvo", "As alterações foram salvas com sucesso!", QMessageBox.Icon.Information)
        dialog.accept()

    def create_export_button(self, text, icon_name=None, export_func=None):
        """Cria um botão de exportação com estilo padronizado"""
        button = QPushButton(text)

        # Configurar o botão usando StyleManager em vez de CSS
        StyleManager.configure_button(button, 'secondary')

        # Adicionar ícone se fornecido
        if icon_name:
            button.setIcon(QIcon.fromTheme(icon_name, QIcon()))
            button.setIconSize(QSize(18, 18))

        if export_func:
            button.clicked.connect(export_func)

        return button

    def update_summary(self):
        """Atualiza o resumo com base nos arquivos carregados"""
        summary_html = "<div style='padding: 10px;'>"

        if self.multas_file:
            summary_multas = get_summary(self.multas_df)
            summary_html += (
                "<h4>Relatório de Multas:</h4>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Linhas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_multas['num_rows']}</td></tr>"
                f"<tr><td>Pessoas únicas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_multas['num_unique_users']}</td></tr>"
                f"<tr><td>Total de multas:</td><td style='color: #f57c00; font-weight: bold;'>R$ {summary_multas['total_fines'] if isinstance(summary_multas['total_fines'], (int, float)) else 0:.2f}</td></tr>"
                "</table>"
            )

        if self.pendencias_file:
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
        self.summary_label.setText(summary_html)


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