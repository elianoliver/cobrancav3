import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFrame,
    QSplitter,
    QGroupBox,
    QProgressBar,
)
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon, QPixmap, QCursor
from PyQt5.QtCore import Qt, QSize, QTimer
import pandas as pd
from modules.read_excel import read_excel_file, get_users_with_fines, get_summary
import os

class ClickableDropArea(QFrame):
    """Área de arrastar e soltar personalizável que também é clicável"""
    def __init__(self, main_window=None):
        super().__init__()
        self.setObjectName("dropArea")
        self.setMinimumHeight(100)
        self.setCursor(QCursor(Qt.PointingHandCursor))  # Muda o cursor para indicar que é clicável
        self.main_window = main_window  # Referência à janela principal

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.icon_label = QLabel("📂")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setObjectName("dropIcon")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Arraste o arquivo Excel aqui ou clique para procurar")
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)

    def mousePressEvent(self, event):
        """Chamado quando a área é clicada"""
        if self.main_window:
            self.main_window.browse_file()


class ExcelInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biblioteca System - Processador de Multas")
        self.setGeometry(100, 100, 900, 600)
        self.setAcceptDrops(True)
        self.file_path = None
        self.setup_ui()
        self.verificar_data = True  # Configuração padrão para verificar a data

        # Exibe uma mensagem de boas-vindas
        QTimer.singleShot(500, self.show_welcome_message)

    def setup_ui(self):
        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout principal (vertical)
        main_layout = QVBoxLayout()
        self.central_widget.setLayout(main_layout)

        # Cabeçalho
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout()
        header_frame.setLayout(header_layout)

        # Logo ou título
        logo_label = QLabel("📚 Biblioteca System")
        logo_label.setObjectName("logoLabel")
        header_layout.addWidget(logo_label)

        # Espaçador flexível
        header_layout.addStretch()

        # Status do arquivo
        self.file_status = QLabel("Nenhum arquivo carregado")
        self.file_status.setObjectName("fileStatus")
        header_layout.addWidget(self.file_status)

        main_layout.addWidget(header_frame)

        # Splitter para dividir a área de trabalho
        splitter = QSplitter(Qt.Horizontal)

        # Painel esquerdo - Controles
        control_panel = QGroupBox("Controles")
        control_panel.setObjectName("controlPanel")
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)

        # Área de instruções
        instruction_frame = QFrame()
        instruction_frame.setObjectName("instructionFrame")
        instruction_layout = QVBoxLayout()
        instruction_frame.setLayout(instruction_layout)

        instruction_label = QLabel("Selecione um arquivo Excel:")
        instruction_label.setWordWrap(True)
        instruction_layout.addWidget(instruction_label)

        # Área de drop clicável para arquivos - passando referência à janela principal
        self.drop_area = ClickableDropArea(main_window=self)
        instruction_layout.addWidget(self.drop_area)

        control_layout.addWidget(instruction_frame)

        # Botões de controle
        button_frame = QFrame()
        button_layout = QVBoxLayout()
        button_frame.setLayout(button_layout)

        self.process_button = QPushButton("⚡ Processar Arquivo")
        self.process_button.clicked.connect(self.process_file)
        button_layout.addWidget(self.process_button)

        # Barra de progresso para feedback visual
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)

        control_layout.addWidget(button_frame)

        # Opção para verificar data do arquivo
        self.check_date_box = QGroupBox("Configurações")
        check_date_layout = QVBoxLayout()
        self.check_date_box.setLayout(check_date_layout)

        from PyQt5.QtWidgets import QCheckBox
        self.date_check = QCheckBox("Verificar se o arquivo é do dia atual")
        self.date_check.setChecked(True)
        self.date_check.toggled.connect(self.toggle_date_check)
        check_date_layout.addWidget(self.date_check)

        control_layout.addWidget(self.check_date_box)

        # Resumo do arquivo
        summary_box = QGroupBox("Resumo do Arquivo")
        summary_box.setObjectName("summaryBox")
        summary_layout = QVBoxLayout()
        summary_box.setLayout(summary_layout)

        self.summary_label = QLabel("Carregue um arquivo para ver o resumo")
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.RichText)
        self.summary_label.setObjectName("summaryLabel")
        summary_layout.addWidget(self.summary_label)

        control_layout.addWidget(summary_box)

        # Adicionar um espaçador para empurrar tudo para cima
        control_layout.addStretch()

        # Painel direito - Resultados
        result_panel = QGroupBox("Resultados")
        result_panel.setObjectName("resultPanel")
        result_layout = QVBoxLayout()
        result_panel.setLayout(result_layout)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setPlaceholderText("Os resultados do processamento aparecerão aqui...")
        result_layout.addWidget(self.result_area)

        # Adicionar os painéis ao splitter
        splitter.addWidget(control_panel)
        splitter.addWidget(result_panel)

        # Definir proporções iniciais do splitter (30% controle, 70% resultados)
        splitter.setSizes([300, 600])

        main_layout.addWidget(splitter)

        # Rodapé com informações
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_layout = QHBoxLayout()
        footer_frame.setLayout(footer_layout)

        footer_text = QLabel("© 2025 Biblioteca System | Versão 1.0")
        footer_text.setObjectName("footerText")
        footer_layout.addWidget(footer_text)

        main_layout.addWidget(footer_frame)

        # Aplicar estilos
        self.apply_styles()

    def apply_styles(self):
        # Estilo moderno e clean
        self.setStyleSheet("""
            QMainWindow, QWidget {
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            #headerFrame {
                background-color: #1e88e5;
                border-radius: 8px;
                max-height: 100px;
                min-height: 60px;
                padding: 0 15px;
            }

            #logoLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
            }

            #fileStatus {
                color: white;
                font-size: 14px;
            }

            QGroupBox {
                font-weight: bold;
                border: 1px solid #dddddd;
                border-radius: 8px;
                margin-top: 15px;
                background-color: white;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1e88e5;
            }

            #instructionFrame {
                background-color: transparent;
                padding: 10px;
            }

            #dropArea {
                border: 2px dashed #1e88e5;
                border-radius: 8px;
                background-color: rgba(30, 136, 229, 0.1);
                margin: 5px;
                min-height: 120px;
                transition: background-color 0.3s;
            }

            #dropArea:hover {
                background-color: rgba(30, 136, 229, 0.2);
                border: 2px solid #1e88e5;
            }

            #dropIcon {
                font-size: 40px;
                color: #1e88e5;
            }

            QPushButton {
                background-color: #1e88e5;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
                border: none;
            }

            QPushButton:hover {
                background-color: #1976d2;
            }

            QPushButton:pressed {
                background-color: #1565c0;
            }

            #summaryLabel {
                padding: 10px;
                background-color: rgba(30, 136, 229, 0.05);
                border-radius: 4px;
            }

            QTextEdit {
                border: 1px solid #dddddd;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                selection-background-color: #1e88e5;
                selection-color: white;
            }

            QProgressBar {
                border: 1px solid #dddddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f5f5f5;
            }

            QProgressBar::chunk {
                background-color: #1e88e5;
                width: 10px;
                margin: 1px;
            }

            #footerFrame {
                max-height: 30px;
                min-height: 30px;
                background-color: #eeeeee;
                border-top: 1px solid #dddddd;
            }

            #footerText {
                color: #666666;
                font-size: 12px;
            }
        """)

    def show_welcome_message(self):
        """Exibe uma mensagem de boas-vindas ao iniciar o aplicativo."""
        welcome_message = (
            "<h2>Bem-vindo ao Processador de Multas</h2>"
            "<p>Este aplicativo processa arquivos Excel para verificar multas pendentes da biblioteca.</p>"
            "<h3>Como gerar o relatório correto:</h3>"
            "<ol>"
            "<li>Acesse o menu 'Circulação de Materiais'</li>"
            "<li>Selecione 'Multas - Pendentes (86)'</li>"
            "<li>Escolha a unidade de informação desejada</li>"
            "<li>Configure o período desejado (data inicial e final)</li>"
            "<li>Marque a opção 'Multas, armários e serviços pendentes'</li>"
            "<li>Gere e salve o relatório em formato Excel</li>"
            "</ol>"
            "<h3>Como usar este aplicativo:</h3>"
            "<p>Arraste o arquivo Excel gerado para a área indicada ou clique para selecioná-lo.</p>"
            "<p><strong>Importante:</strong> Por padrão, apenas relatórios gerados hoje serão aceitos. "
            "Para processar relatórios de outras datas, desmarque a opção 'Verificar se o arquivo é do dia atual'.</p>"
        )
        self.result_area.setHtml(welcome_message)

    def show_message(self, title, message, icon=QMessageBox.Information):
        """Exibe um QMessageBox com estilo adequado."""
        msg_box = QMessageBox(self)
        msg_box.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 14px;
                min-width: 300px;
            }
            QPushButton {
                background-color: #1e88e5;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QMessageBox {
                background-color: #f5f5f5;
            }
        """)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Permite a entrada de arquivos arrastados."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Manipula arquivos soltos na interface."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith((".xlsx", ".xls")):
                self.file_path = file_path
                self.file_status.setText(f"Arquivo: {os.path.basename(file_path)}")
                self.update_summary(file_path)

                # Efeito visual para feedback
                self.animate_progress()
            else:
                self.show_message(
                    "Formato Inválido",
                    "Por favor, arraste um arquivo Excel válido (.xlsx ou .xls).",
                    QMessageBox.Warning
                )

    def animate_progress(self):
        """Anima a barra de progresso para dar feedback visual."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        for i in range(101):
            QTimer.singleShot(i * 10, lambda v=i: self.progress_bar.setValue(v))

        QTimer.singleShot(1100, lambda: self.progress_bar.setVisible(False))

    def browse_file(self):
        """Abre uma janela de diálogo para selecionar o arquivo Excel."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecione o arquivo Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_path = file_path
            self.file_status.setText(f"Arquivo: {os.path.basename(file_path)}")
            self.update_summary(file_path)
            self.animate_progress()

    def toggle_date_check(self, checked):
        """Alterna a configuração de verificação de data"""
        self.verificar_data = checked
        if checked:
            self.show_message("Verificação Ativada", "A verificação de data está ativada. Apenas arquivos do dia atual serão processados.")
        else:
            self.show_message("Verificação Desativada", "Atenção: A verificação de data está desativada. Arquivos com qualquer data serão processados.", QMessageBox.Warning)

    def update_summary(self, file_path):
        try:
            df = read_excel_file(file_path, verificar_data=self.verificar_data)
            summary = get_summary(df)

            # Personalizando o texto do resumo com base no retorno de get_summary
            styled_summary = (
                "<div style='padding: 10px;'>"
                "<table style='width: 100%; border-collapse: collapse;'>"
                f"<tr><td>Linhas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary['num_rows']}</td></tr>"
                f"<tr><td>Pessoas únicas:</td><td style='color: #2e7d32; font-weight: bold;'>{summary['num_unique_users']}</td></tr>"
                f"<tr><td>Total de multas:</td><td style='color: #f57c00; font-weight: bold;'>R$ {summary['total_fines']:.2f}</td></tr>"
                "</table>"
                "</div>"
            )

            # Aplicar o texto estilizado com suporte a HTML
            self.summary_label.setText(styled_summary)
            self.summary_label.setWordWrap(True)

        except ValueError as e:
            if "não é do dia atual" in str(e):
                error_summary = (
                    "<div style='padding: 10px;'>"
                    "<h3 style='color: #e53935; margin: 0 0 10px 0;'>⚠️ Erro de Data</h3>"
                    f"<p>{str(e)}</p>"
                    "<p>Desmarque a opção 'Verificar se o arquivo é do dia atual' para processar este arquivo.</p>"
                    "</div>"
                )
                self.summary_label.setText(error_summary)
                self.show_message("Erro de Data", str(e), QMessageBox.Warning)
            else:
                self._handle_generic_error(e)
        except Exception as e:
            self._handle_generic_error(e)

    def _handle_generic_error(self, e):
        """Método auxiliar para tratar erros genéricos"""
        error_summary = (
            "<div style='padding: 10px;'>"
            "<h3 style='color: #e53935; margin: 0 0 10px 0;'>⚠️ Erro no Processamento</h3>"
            "<p>Não foi possível processar o arquivo. Verifique se o formato está correto.</p>"
            "</div>"
        )
        self.summary_label.setText(error_summary)
        self.show_message("Erro", f"Erro ao processar o arquivo: {str(e)}", QMessageBox.Critical)

    def process_file(self):
        """Processa o arquivo Excel com o caminho fornecido."""
        if not self.file_path:
            self.show_message("Erro", "Por favor, carregue um arquivo Excel primeiro.", QMessageBox.Warning)
            return

        try:
            # Mostra feedback visual
            self.animate_progress()

            # Lê e processa o arquivo Excel - agora passando explicitamente a configuração de verificação de data
            df = read_excel_file(self.file_path, verificar_data=self.verificar_data)
            users_with_fines = get_users_with_fines(df)

            # Exibe os resultados na área de texto
            if not users_with_fines.empty:
                # Formata os resultados como HTML para melhor visualização
                html_result = "<h3>Usuários com Multas Encontrados</h3>"

                # Converter o DataFrame para HTML com estilos
                html_table = users_with_fines.to_html(
                    classes='data-table',
                    index=False,
                    border=0
                ).replace('<table', '<table style="width:100%; border-collapse: collapse; margin-top: 10px;"'
                ).replace('<th', '<th style="background-color: #1e88e5; color: white; padding: 8px; text-align: left;"'
                ).replace('<td', '<td style="border: 1px solid #ddd; padding: 8px;"'
                ).replace('<tr>', '<tr style="background-color: #f5f5f5;">')

                html_result += html_table
                self.result_area.setHtml(html_result)
            else:
                self.result_area.setHtml("<h3>Resultado</h3><p>Nenhum usuário com multas encontrado.</p>")

            self.show_message("Sucesso", "Arquivo processado com sucesso!")

        except Exception as e:
            self.show_message("Erro", f"Erro ao processar o arquivo: {str(e)}", QMessageBox.Critical)


def main():
    """Inicia a interface gráfica com PyQt5."""
    app = QApplication(sys.argv)
    window = ExcelInterface()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()