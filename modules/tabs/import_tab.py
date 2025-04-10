from PyQt6.QtWidgets import (
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
    QFrame, QGroupBox, QMessageBox, QProgressBar
)
from PyQt6.QtGui import QIcon, QFont, QCursor, QPalette, QColor
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
import pandas as pd
import os

from modules.tabs.base_tab import BaseTab
from modules.styles_fix import StyleManager, AppColors
from modules.read_excel import read_excel_file, clean_column_names, get_summary
from modules.components import FileDropArea
from modules.config_manager import ConfigManager

class ImportTab(BaseTab):
    """Aba para importação e carregamento dos arquivos Excel."""

    # Sinais específicos desta aba
    files_loaded = pyqtSignal(pd.DataFrame, pd.DataFrame, str, str)  # multas_df, pendencias_df, multas_file, pendencias_file
    unify_requested = pyqtSignal()

    def __init__(self, parent=None):
        self.multas_df = None
        self.pendencias_df = None
        self.verificar_data = True
        self.multas_file = None
        self.pendencias_file = None
        self.config_manager = ConfigManager()

        super().__init__(parent)

    def setup_ui(self):
        """Configura a interface da aba de importação."""
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

        self.layout.addWidget(header_container)

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

        self.layout.addWidget(instructions_card)

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

        self.layout.addWidget(date_check_container)

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
        self.layout.addWidget(drop_container, 1)

        # Container para botão de unificação e progresso
        action_container = QFrame()
        action_container.setObjectName("actionContainer")
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

        self.layout.addWidget(action_container)

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

            # Emitir sinal para atualizar resumo
            if self.multas_df is not None and self.pendencias_df is not None:
                self.files_loaded.emit(self.multas_df, self.pendencias_df, self.multas_file, self.pendencias_file)

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
                self.show_message_box("Erro de Data", error_summary, QMessageBox.Icon.Warning)

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

    def _handle_generic_error(self, e):
        """Método auxiliar para tratar erros genéricos"""
        self.show_message_box("Erro", f"Erro no processamento: {str(e)}", QMessageBox.Icon.Critical)

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

    def unify_reports(self):
        """Solicita a unificação dos relatórios"""
        # Parar efeito de pulso quando o botão for clicado
        self.stop_button_pulse_effect(self.unify_button)

        if not (self.multas_df is not None and self.pendencias_df is not None):
            self.show_message_box(
                "Erro",
                "É necessário carregar os dois relatórios antes de unificá-los.",
                QMessageBox.Icon.Warning
            )
            return

        # Emitir sinal de unificação solicitada
        self.unify_requested.emit()