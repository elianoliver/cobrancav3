import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QTextEdit,
    QMessageBox, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QSplitter,
    QGroupBox, QProgressBar, QRadioButton, QButtonGroup, QTabWidget, QGridLayout, QTabWidget, QTextBrowser, QDialog
)
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon, QPixmap, QCursor
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
import pandas as pd
from modules.read_excel import read_excel_file, clean_column_names, get_summary, unify_dataframes
from modules.data_processor import generate_json_file, filter_users_by_category, categorize_users
from modules.styles import get_drop_area_style, get_status_label_style
from modules.styles import get_main_styles, get_welcome_html, get_categories_html
import json

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

class FileDropArea(QFrame):
    """Área de arrastar e soltar para arquivos Excel com identificação do tipo"""
    fileDropped = pyqtSignal(str, str)  # Sinal que emite caminho do arquivo e tipo

    def __init__(self, report_type="multas", parent=None):
        super().__init__(parent)
        self.setObjectName("dropArea")
        self.setMinimumHeight(100)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.report_type = report_type  # 'multas' ou 'pendencias'
        self.file_path = None

        # Layout e componentes visuais
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Ícone diferente para cada tipo de relatório
        icon = "💰" if self.report_type == "multas" else "📚"
        self.icon_label = QLabel(icon)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setObjectName("dropIcon")
        layout.addWidget(self.icon_label)

        # Descrição do tipo de relatório
        title = "Relatório de Multas (86)" if self.report_type == "multas" else "Relatório de Pendências (76)"
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("dropTitle")
        layout.addWidget(self.title_label)

        # Instrução
        self.text_label = QLabel("Arraste o arquivo Excel aqui ou clique para procurar")
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)

        # Status do arquivo
        self.status_label = QLabel("Nenhum arquivo selecionado")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("fileStatusLabel")
        layout.addWidget(self.status_label)

        # Aplicar estilos usando o módulo de estilos
        self.setStyleSheet(get_drop_area_style(self.report_type))

    def set_file(self, file_path):
        """Define o arquivo e atualiza o visual"""
        self.file_path = file_path
        if file_path:
            self.status_label.setText(f"Arquivo: {os.path.basename(file_path)}")
            self.status_label.setStyleSheet(get_status_label_style(True))
        else:
            self.status_label.setText("Nenhum arquivo selecionado")
            self.status_label.setStyleSheet(get_status_label_style(False))

    def mousePressEvent(self, event):
        """Quando clicado, abre diálogo para selecionar arquivo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Selecione o {self.title_label.text()}", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.set_file(file_path)
            self.fileDropped.emit(file_path, self.report_type)

    def dragEnterEvent(self, event):
        """Permite a entrada de arquivos arrastados"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Processa o arquivo quando solto na área"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith((".xlsx", ".xls")):
                self.set_file(file_path)
                self.fileDropped.emit(file_path, self.report_type)
            else:
                QMessageBox.warning(self, "Formato Inválido",
                                   "Por favor, arraste um arquivo Excel válido (.xlsx ou .xls).")


class ExcelInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biblioteca System - Envio de Multas e Pendências")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(False)  # Desabilita o arraste global

        # Inicializar o gerenciador de configuração
        self.config_manager = ConfigManager()

        # Armazenar caminhos dos arquivos
        self.multas_file = None
        self.pendencias_file = None
        self.verificar_data = True

        # Dataframes dos relatórios
        self.df_multas = None
        self.df_pendencias = None
        self.df_unificado = None

        self.setup_ui()

        # Exibe mensagem de boas-vindas
        QTimer.singleShot(500, self.show_welcome_message)

    def setup_ui(self):
        """Configura a interface do usuário"""
        # Widget principal
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Criar tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)

        # Setup das abas
        self.setup_import_tab()
        self.setup_results_tab()
        self.setup_summary_tab()
        self.setup_template_tab()  # Substitui a aba de categorias por templates
        self.setup_export_tab()

        # Adicionar as tabs ao layout principal
        main_layout.addWidget(self.tabs)

        # Definir o tamanho inicial da janela
        self.resize(1200, 800)

        # Estilizar a aplicação
        self.setStyleSheet(get_main_styles())

    def setup_import_tab(self):
        """Configura a aba de importação de arquivos"""
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)

        # Cabeçalho com título e descrição
        header = QLabel("Importação de Relatórios")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        header.setAlignment(Qt.AlignCenter)
        import_layout.addWidget(header)

        description = QLabel(
            "Arraste e solte os arquivos Excel dos relatórios 86 (Multas) e 76 (Pendências) "
            "ou clique nas áreas abaixo para selecionar os arquivos."
        )
        description.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        import_layout.addWidget(description)

        # Opção para verificar data dos arquivos
        date_check_layout = QHBoxLayout()
        date_check_layout.addStretch()
        self.check_date = QPushButton("Verificar se os arquivos são do dia atual")
        self.check_date.setCheckable(True)
        self.check_date.setChecked(True)
        self.check_date.clicked.connect(self.toggle_date_check)
        date_check_layout.addWidget(self.check_date)
        date_check_layout.addStretch()
        import_layout.addLayout(date_check_layout)

        # Container para as áreas de drop
        drop_container = QWidget()
        drop_layout = QHBoxLayout(drop_container)

        # Área de drop para relatório de multas (86)
        self.multas_drop_area = FileDropArea(report_type="multas")
        self.multas_drop_area.fileDropped.connect(self.handle_file_dropped)
        drop_layout.addWidget(self.multas_drop_area)

        # Área de drop para relatório de pendências (76)
        self.pendencias_drop_area = FileDropArea(report_type="pendencias")
        self.pendencias_drop_area.fileDropped.connect(self.handle_file_dropped)
        drop_layout.addWidget(self.pendencias_drop_area)

        # Adicionar container ao layout principal
        import_layout.addWidget(drop_container)

        # Botão para unificar relatórios
        unify_container = QWidget()
        unify_layout = QHBoxLayout(unify_container)
        unify_layout.addStretch()

        self.unify_button = QPushButton("Unificar Relatórios")
        self.unify_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.unify_button.setEnabled(False)
        self.unify_button.clicked.connect(self.unify_reports)
        unify_layout.addWidget(self.unify_button)
        unify_layout.addStretch()

        import_layout.addWidget(unify_container)

        # Barra de progresso (inicialmente oculta)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                width: 5px;
            }
        """)
        import_layout.addWidget(self.progress_bar)

        # Espaçador para empurrar tudo para cima
        import_layout.addStretch()

        # Adicionar a aba ao widget de abas
        self.tabs.addTab(import_tab, "Importação de Arquivos")

    def setup_results_tab(self):
        """Configura a aba de resultados"""
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)

        # Área de resultados
        self.result_area = QTextBrowser()
        self.result_area.setOpenExternalLinks(True)  # Permite abrir links
        results_layout.addWidget(self.result_area)

        # Adicionar a aba ao widget principal
        self.tabs.addTab(results_tab, "Resultados")

    def setup_summary_tab(self):
        """Configura a aba de resumo"""
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)

        # Cabeçalho
        header = QLabel("Resumo dos Dados")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        header.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(header)

        # Descrição
        description = QLabel("Estatísticas dos relatórios carregados:")
        description.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        summary_layout.addWidget(description)

        # Área de resumo
        self.summary_label = QTextBrowser()
        self.summary_label.setStyleSheet("font-size: 14px;")
        summary_layout.addWidget(self.summary_label)

        # Adicionar a aba ao widget principal
        self.tabs.addTab(summary_tab, "Resumo")

    def setup_template_tab(self):
        """Configura a aba de templates de email"""
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)

        # Adicionar cabeçalho
        header = QLabel("Templates de Email")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        header.setAlignment(Qt.AlignCenter)
        template_layout.addWidget(header)

        # Adicionar descrição
        description = QLabel("Selecione o tipo de notificação e personalize o template:")
        description.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        template_layout.addWidget(description)

        # Container para os controles
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)

        # Grupo de radio buttons para os tipos de template
        radio_group = QGroupBox("Tipo de Notificação")
        radio_layout = QVBoxLayout(radio_group)

        # Criar os radio buttons
        self.rb_apenas_multa = QRadioButton("Apenas Multa")
        self.rb_apenas_multa.setObjectName("rb1")
        self.rb_apenas_multa.setChecked(True)  # Selecionado por padrão
        self.rb_apenas_pendencia = QRadioButton("Apenas Pendência")
        self.rb_apenas_pendencia.setObjectName("rb2")
        self.rb_multa_e_pendencia = QRadioButton("Multa e Pendência")
        self.rb_multa_e_pendencia.setObjectName("rb3")

        # Adicionar os radio buttons ao grupo
        radio_layout.addWidget(self.rb_apenas_multa)
        radio_layout.addWidget(self.rb_apenas_pendencia)
        radio_layout.addWidget(self.rb_multa_e_pendencia)

        # Configurar a largura máxima do grupo
        radio_group.setMaximumWidth(250)

        # Adicionar o grupo ao layout de controles
        controls_layout.addWidget(radio_group)

        # Criar botão para copiar o template
        copy_button = QPushButton("Copiar Template")
        copy_button.setIcon(QIcon.fromTheme("edit-copy"))
        copy_button.setToolTip("Copiar o template para a área de transferência")
        copy_button.setMinimumWidth(150)
        copy_button.setMaximumHeight(50)
        copy_button.clicked.connect(self.copy_template)

        # Criar botão para editar o template
        edit_button = QPushButton("Editar Template")
        edit_button.setIcon(QIcon.fromTheme("edit"))
        edit_button.setToolTip("Editar o template atual")
        edit_button.setMinimumWidth(150)
        edit_button.setMaximumHeight(50)
        edit_button.clicked.connect(self.edit_template)

        # Adicionar botões ao layout com um espaçador
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(copy_button)
        button_layout.addWidget(edit_button)
        button_layout.addStretch()

        # Adicionar o container do botão ao layout de controles
        controls_layout.addWidget(button_container)

        # Adicionar o container de controles ao layout principal
        template_layout.addWidget(controls_container)

        # Área de exibição do template
        self.template_area = QTextBrowser()
        self.template_area.setOpenExternalLinks(True)  # Permitir abrir links
        self.template_area.setStyleSheet("font-size: 14px; border: 1px solid #ccc; border-radius: 5px; padding: 10px;")
        template_layout.addWidget(self.template_area)

        # Conectar eventos dos radio buttons
        self.rb_apenas_multa.toggled.connect(lambda: self.update_template(self.rb_apenas_multa) if self.rb_apenas_multa.isChecked() else None)
        self.rb_apenas_pendencia.toggled.connect(lambda: self.update_template(self.rb_apenas_pendencia) if self.rb_apenas_pendencia.isChecked() else None)
        self.rb_multa_e_pendencia.toggled.connect(lambda: self.update_template(self.rb_multa_e_pendencia) if self.rb_multa_e_pendencia.isChecked() else None)

        # Exibir o template inicial
        self.show_template_apenas_multa()

        # Adicionar a aba ao widget principal
        self.tabs.addTab(template_tab, "Templates de Email")

    def setup_export_tab(self):
        """Configura a aba de exportação"""
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)

        # Cabeçalho
        header = QLabel("Exportação de Dados")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        header.setAlignment(Qt.AlignCenter)
        export_layout.addWidget(header)

        # Descrição
        description = QLabel(
            "Exporte os dados unificados em formato JSON para uso com outras ferramentas."
        )
        description.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        export_layout.addWidget(description)

        # Botão de exportação
        export_button_container = QWidget()
        export_button_layout = QHBoxLayout(export_button_container)
        export_button_layout.addStretch()

        self.export_button = QPushButton("Exportar para JSON")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_json)
        export_button_layout.addWidget(self.export_button)
        export_button_layout.addStretch()

        export_layout.addWidget(export_button_container)
        export_layout.addStretch()

        # Adicionar a aba ao widget principal
        self.tabs.addTab(export_tab, "Exportação")

    def handle_file_dropped(self, file_path, report_type):
        """Manipula quando um arquivo é solto ou selecionado em uma área de drop"""
        try:
            # Verificar data do arquivo
            df = read_excel_file(file_path, verificar_data=self.verificar_data)
            df = clean_column_names(df)

            # Atribuir ao tipo correto
            if report_type == "multas":
                self.multas_file = file_path
                self.df_multas = df
                self.animate_progress()
            else:
                self.pendencias_file = file_path
                self.df_pendencias = df
                self.animate_progress()

            # Atualizar resumo
            self.update_summary()

            # Habilitar botão de unificação se ambos os arquivos estiverem carregados
            self.unify_button.setEnabled(bool(self.multas_file and self.pendencias_file))

        except ValueError as e:
            if "não é do dia atual" in str(e):
                error_summary = (
                    f"⚠️ Erro de Data no relatório de {report_type.capitalize()}: {str(e)}\n"
                    "Desmarque a opção 'Verificar se os arquivos são do dia atual' para processar este arquivo."
                )
                self.show_message("Erro de Data", error_summary, QMessageBox.Warning)

                # Remover referência ao arquivo com erro
                if report_type == "multas":
                    self.multas_file = None
                    self.multas_drop_area.set_file(None)
                else:
                    self.pendencias_file = None
                    self.pendencias_drop_area.set_file(None)
            else:
                self._handle_generic_error(e)
        except Exception as e:
            self._handle_generic_error(e)

    def update_summary(self):
        """Atualiza o resumo com base nos arquivos carregados"""
        summary_html = "<div style='padding: 10px;'>"

        if self.multas_file:
            summary_multas = get_summary(self.df_multas)
            summary_html += (
                "<h4>Relatório de Multas:</h4>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Linhas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_multas['num_rows']}</td></tr>"
                f"<tr><td>Pessoas únicas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_multas['num_unique_users']}</td></tr>"
                f"<tr><td>Total de multas:</td><td style='color: #f57c00; font-weight: bold;'>R$ {summary_multas['total_fines'] if isinstance(summary_multas['total_fines'], (int, float)) else 0:.2f}</td></tr>"
                "</table>"
            )

        if self.pendencias_file:
            summary_pendencias = get_summary(self.df_pendencias)
            summary_html += (
                "<h4>Relatório de Pendências:</h4>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Linhas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_pendencias['num_rows']}</td></tr>"
                f"<tr><td>Pessoas únicas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary_pendencias['num_unique_users']}</td></tr>"
                "</table>"
            )

        if self.df_unificado is not None:
            # Encontrar a coluna correta para contagem de usuários
            if 'Código da pessoa' in self.df_unificado.columns and not self.df_unificado['Código da pessoa'].isna().all():
                total_users = self.df_unificado['Código da pessoa'].nunique()
            else:
                total_users = 0  # Valor padrão se não encontrar coluna válida

            summary_html += (
                "<h4>Dados Unificados:</h4>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Total de registros:</td><td style='color: #2e7d32; font-weight: bold;'>{len(self.df_unificado)}</td></tr>"
                f"<tr><td>Total de usuários:</td><td style='color: #2e7d32; font-weight: bold;'>{total_users}</td></tr>"
                "</table>"
            )

        summary_html += "</div>"
        self.summary_label.setText(summary_html)

    def unify_reports(self):
        """Unifica os dois relatórios em um único DataFrame"""
        if not (self.df_multas is not None and self.df_pendencias is not None):
            self.show_message(
                "Erro",
                "É necessário carregar os dois relatórios antes de unificá-los.",
                QMessageBox.Warning
            )
            return

        try:
            # Mostrar feedback visual
            self.animate_progress()

            # Chamar a função modularizada de unificação
            self.df_unificado = unify_dataframes(self.df_multas, self.df_pendencias)

            # Gerar arquivo xlsx
            self.df_unificado.to_excel('unificado.xlsx', index=False)

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
            self.show_message("Erro", f"Erro ao unificar relatórios: {str(e)}", QMessageBox.Critical)

    def display_unified_results(self):
        """Exibe os resultados da unificação em formato de dashboard"""
        if self.df_unificado is None:
            return

        # Obter categorias e estatísticas
        categories = categorize_users(self.df_unificado)

        # Calcular estatísticas para os botões
        df_rel86 = self.df_unificado[self.df_unificado['Relatório'] == 'rel86']
        df_rel76 = self.df_unificado[self.df_unificado['Relatório'] == 'rel76']

        # Contagens de pessoas únicas
        unique_users_rel86 = df_rel86['Código da pessoa'].nunique() if 'Código da pessoa' in df_rel86.columns else 0
        unique_users_rel76 = df_rel76['Código da pessoa'].nunique() if 'Código da pessoa' in df_rel76.columns else 0

        # Filtrar registros com chaves emprestadas
        chaves_df = self.df_unificado[
            (~self.df_unificado['Número chave'].isna()) &
            (self.df_unificado['Número chave'].str.strip() != "")
        ]

        # Quantidade de pessoas únicas com chaves
        unique_users_chaves = chaves_df['Código da pessoa'].nunique() if 'Código da pessoa' in chaves_df.columns else 0

        # HTML simplificado para o dashboard com cards recolhíveis (sem tabelas de detalhes)
        dashboard_html = """
        <div style='font-family: Arial, sans-serif; padding: 20px;'>
            <h2 style='color: #2c3e50; text-align: center; margin-bottom: 25px;'>Dashboard de Relatórios</h2>

            <div style='display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;'>
                <!-- Card do Relatório 86 (recolhível) -->
                <div id="card_rel86" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden; transition: all 0.3s ease;'>
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
                <div id="card_rel76" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden; transition: all 0.3s ease;'>
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
                <div id="card_sem_email" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden; transition: all 0.3s ease;'>
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
                <div id="card_chaves" class="dashboard_card" style='width: 45%; background-color: white; color: #333; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); overflow: hidden; transition: all 0.3s ease;'>
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
        if self.df_unificado is None:
            return

        # Obter categorias
        categories = categorize_users(self.df_unificado)

        # Criar HTML para exibição
        html = """
        <div style='font-family: Arial; font-size: 14px;'>
            <h2 style='color: #2c3e50;'>Relatórios e Estatísticas</h2>

            <!-- Relatório 86 (Multas) -->
            <div style='margin-bottom: 30px; border: 1px solid #3498db; border-radius: 5px; padding: 15px;'>
                <h3 style='color: #3498db; margin-top: 0;'>📊 Relatório 86 (Multas)</h3>
                <ul style='list-style-type: none; padding-left: 10px;'>
                    <li><strong>Número total de linhas:</strong> {rel86_linhas}</li>
                    <li><strong>Número total de pessoas únicas sem email:</strong> {rel86_pessoas_sem_email}</li>
                    <li><strong>Valor total de multas:</strong> R$ {rel86_total_multas:.2f}</li>
                </ul>
            </div>

            <!-- Relatório 76 (Pendências) -->
            <div style='margin-bottom: 30px; border: 1px solid #e74c3c; border-radius: 5px; padding: 15px;'>
                <h3 style='color: #e74c3c; margin-top: 0;'>📚 Relatório 76 (Pendências)</h3>
                <ul style='list-style-type: none; padding-left: 10px;'>
                    <li><strong>Número total de linhas:</strong> {rel76_linhas}</li>
                    <li><strong>Número total de pessoas únicas sem email:</strong> {rel76_pessoas_sem_email}</li>
                </ul>

                <!-- Lista ordenada de dias de atraso -->
                <h4 style='color: #e74c3c;'>Lista de Atrasos (do maior para o menor)</h4>
                <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
                    <thead>
                        <tr style='background-color: #e74c3c; color: white;'>
                            <th style='padding: 8px; text-align: left;'>Matrícula</th>
                            <th style='padding: 8px; text-align: left;'>Nome</th>
                            <th style='padding: 8px; text-align: center;'>Dias de Atraso</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rel76_dias_atraso_rows}
                    </tbody>
                </table>
            </div>

            <!-- Pessoas Sem Email -->
            <div style='margin-bottom: 30px; border: 1px solid #27ae60; border-radius: 5px; padding: 15px;'>
                <h3 style='color: #27ae60; margin-top: 0;'>👤 Pessoas Sem Email</h3>
                <p><strong>Total de pessoas sem email:</strong> {pessoas_sem_email}</p>

                <table style='width: 100%; border-collapse: collapse; margin-top: 10px;'>
                    <thead>
                        <tr style='background-color: #27ae60; color: white;'>
                            <th style='padding: 8px; text-align: left;'>Matrícula</th>
                            <th style='padding: 8px; text-align: left;'>Nome</th>
                        </tr>
                    </thead>
                    <tbody>
                        {pessoas_sem_email_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

        # Gerar linhas para a tabela de dias de atraso
        dias_atraso_rows = ""
        for codigo, nome, dias in categories['rel76']['dias_atraso']:
            dias_atraso_rows += f"""
            <tr style='background-color: {"#f9ebea" if dias > 30 else "#fdf2e9"}'>
                <td style='padding: 8px; border-bottom: 1px solid #ddd;'>{codigo}</td>
                <td style='padding: 8px; border-bottom: 1px solid #ddd;'>{nome}</td>
                <td style='padding: 8px; border-bottom: 1px solid #ddd; text-align: center;
                         {"font-weight: bold; color: #c0392b;" if dias > 30 else ""}'>
                    {dias}
                </td>
            </tr>
            """

        if not categories['rel76']['dias_atraso']:
            dias_atraso_rows = """
            <tr>
                <td colspan="3" style='padding: 8px; text-align: center; font-style: italic;'>
                    Nenhum atraso encontrado
                </td>
            </tr>
            """

        # Gerar linhas para a tabela de pessoas sem email
        pessoas_sem_email_rows = ""
        for codigo, nome in categories['sem_email']['pessoas']:
            pessoas_sem_email_rows += f"""
            <tr>
                <td style='padding: 8px; border-bottom: 1px solid #ddd;'>{codigo}</td>
                <td style='padding: 8px; border-bottom: 1px solid #ddd;'>{nome}</td>
            </tr>
            """

        if not categories['sem_email']['pessoas']:
            pessoas_sem_email_rows = """
            <tr>
                <td colspan="2" style='padding: 8px; text-align: center; font-style: italic;'>
                    Nenhuma pessoa sem email encontrada
                </td>
            </tr>
            """

        # Formatar o HTML com os valores
        formatted_html = html.format(
            rel86_linhas=categories['rel86']['total_linhas'],
            rel86_pessoas_sem_email=len(categories['rel86']['pessoas_sem_email']),
            rel86_total_multas=categories['rel86']['total_multas'],
            rel76_linhas=categories['rel76']['total_linhas'],
            rel76_pessoas_sem_email=len(categories['rel76']['pessoas_sem_email']),
            rel76_dias_atraso_rows=dias_atraso_rows,
            pessoas_sem_email=len(categories['sem_email']['pessoas']),
            pessoas_sem_email_rows=pessoas_sem_email_rows
        )

        self.template_area.setHtml(formatted_html)

    def export_json(self):
        """Exporta os dados unificados para um arquivo JSON"""
        if self.df_unificado is None:
            self.show_message("Erro", "Não há dados unificados para exportar.", QMessageBox.Warning)
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
                json_path = generate_json_file(self.df_unificado, output_path)

                # Mostrar mensagem de sucesso
                self.show_message("Sucesso", f"Arquivo JSON gerado com sucesso: {json_path}")

        except Exception as e:
            self.show_message("Erro", f"Erro ao exportar para JSON: {str(e)}", QMessageBox.Critical)

    def toggle_date_check(self, checked):
        """Alterna a configuração de verificação de data"""
        self.verificar_data = checked
        message = (
            "A verificação de data está ativada. Apenas arquivos do dia atual serão processados."
            if checked else
            "Atenção: A verificação de data está desativada. Arquivos com qualquer data serão processados."
        )
        self.show_message(
            "Verificação de Data",
            message,
            QMessageBox.Warning if not checked else QMessageBox.Information
        )

    def animate_progress(self):
        """Anima a barra de progresso para feedback visual"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i in range(101):
            QTimer.singleShot(i * 10, lambda v=i: self.progress_bar.setValue(v))

        QTimer.singleShot(1100, lambda: self.progress_bar.setVisible(False))

    def _handle_generic_error(self, e):
        """Método auxiliar para tratar erros genéricos"""
        self.show_message("Erro", f"Erro no processamento: {str(e)}", QMessageBox.Critical)

    def show_message(self, title, message, icon=QMessageBox.Information):
        """Exibe um QMessageBox com estilo adequado"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    def show_welcome_message(self):
        """Exibe mensagem de boas-vindas"""
        try:
            if hasattr(self, 'result_area') and self.result_area is not None:
                self.result_area.setHtml(get_welcome_html())
            elif hasattr(self, 'template_area') and self.template_area is not None:
                self.template_area.setHtml(get_welcome_html())
        except Exception as e:
            print(f"Erro ao exibir mensagem de boas-vindas: {e}")

    def apply_styles(self):
        # Aplicar estilos do módulo centralizado
        self.setStyleSheet(get_main_styles())

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

        # Template padrão se não tiver nenhum salvo
        template = """
        <div style='font-family: Arial, sans-serif; color: #333; line-height: 1.6;'>
            <h3 style='color: #3498db;'>Template: Notificação de Multa</h3>
            <hr style='border: 1px solid #eee;'>
            <pre style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-family: Consolas, monospace;'>
Prezado(a) {formtext: name=nome; trim=yes; formatter=(value) -> upper(value)},

Conforme estabelecido no [Regulamento Interno das Bibliotecas do Instituto Federal Catarinense](https://biblioteca.ifc.edu.br/wp-content/uploads/sites/53/2023/04/SIBI-Regulamento.pdf), artigo 44, é nossa responsabilidade notificá-lo(a) sobre as pendências em sua conta de usuário na biblioteca.

Constata-se a existência de multa acumulada no valor total de R$ {formtext: name=valor; default=00,00}. referente ao(s) seguinte(s) item(ns):

- {formtext: name=Obra}
    - Data de Empréstimo: {formdate: DD/MM/YYYY; name=emprestimo}
    - Data de Devolução Prevista: {formdate: DD/MM/YYYY; name=prevista}
    - Data de Devolução Efetiva: {formdate: DD/MM/YYYY; name=efetiva}
    - Dias de Atraso: {=datetimediff(datetimeparse(prevista, "DD/MM/YYYY"), datetimeparse(efetiva, "DD/MM/YYYY"), "D")}

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
        self.show_message("Copiado", "Template copiado para a área de transferência!", QMessageBox.Information)

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
        dialog.exec_()

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

        self.show_message("Template Salvo", "As alterações foram salvas com sucesso!", QMessageBox.Information)
        dialog.accept()


def main():
    """Inicia a interface gráfica com PyQt5."""
    app = QApplication(sys.argv)
    window = ExcelInterface()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()