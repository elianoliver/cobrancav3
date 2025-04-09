"""
Módulo para gerenciar estilos da aplicação
Centraliza todos os estilos CSS em um único lugar para facilitar a manutenção
"""

def get_main_styles():
    """Retorna os estilos gerais da aplicação"""
    return """
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

        QPushButton:disabled {
            background-color: #bbdefb;
            color: #90caf9;
        }

        QTextEdit {
            border: 1px solid #dddddd;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
            selection-background-color: #1e88e5;
            selection-color: white;
        }

        QTabWidget::pane {
            border: 1px solid #dddddd;
            border-radius: 4px;
            background-color: white;
        }

        QTabBar::tab {
            background-color: #f5f5f5;
            border: 1px solid #dddddd;
            padding: 8px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected {
            background-color: white;
            border-bottom-color: white;
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
    """

def get_drop_area_style(report_type="multas"):
    """
    Retorna estilos específicos para áreas de arrastar e soltar

    Args:
        report_type: Tipo de relatório ('multas' ou 'pendencias')
    """
    if report_type == "multas":
        return """
            #dropArea {
                border: 2px dashed #1e88e5;
                background-color: rgba(30, 136, 229, 0.1);
            }
            #dropTitle {
                color: #1e88e5;
                font-weight: bold;
            }
            #dropIcon {
                font-size: 24px;
                color: #1e88e5;
            }
        """
    else:
        return """
            #dropArea {
                border: 2px dashed #f57c00;
                background-color: rgba(245, 124, 0, 0.1);
            }
            #dropTitle {
                color: #f57c00;
                font-weight: bold;
            }
            #dropIcon {
                font-size: 24px;
                color: #f57c00;
            }
        """

def get_status_label_style(has_file=False):
    """
    Retorna o estilo para o rótulo de status do arquivo

    Args:
        has_file: Se True, aplica estilo para quando um arquivo está carregado
    """
    if has_file:
        return "color: #2e7d32; font-weight: bold;"
    return ""

def get_welcome_html():
    """Retorna o HTML da mensagem de boas-vindas"""
    return (
        "<h2>Bem-vindo ao Unificador de Relatórios da Biblioteca</h2>"
        "<p>Este aplicativo processa e unifica dados de múltiplos relatórios da biblioteca.</p>"

        "<div style='background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>"
        "<h3 style='margin-top: 0; color: #2e7d32;'>Nova funcionalidade de unificação!</h3>"
        "<p>Agora você pode carregar os dois relatórios principais da biblioteca e unificá-los para uma análise completa:</p>"

        "<div style='display: flex; margin-top: 15px;'>"
        "<div style='flex: 1; background-color: #e3f2fd; padding: 10px; border-radius: 5px; margin-right: 10px;'>"
        "<h4 style='margin-top: 0; color: #1e88e5;'>💰 Relatório de Multas (86)</h4>"
        "<p>Traz informações sobre valores de multas pendentes dos usuários.</p>"
        "</div>"

        "<div style='flex: 1; background-color: #fff8e1; padding: 10px; border-radius: 5px;'>"
        "<h4 style='margin-top: 0; color: #f57c00;'>📚 Relatório de Pendências (76)</h4>"
        "<p>Contém os materiais que ainda não foram devolvidos pelos usuários.</p>"
        "</div>"
        "</div>"
        "</div>"

        "<h3>Como usar:</h3>"
        "<ol>"
        "<li>Carregue os dois relatórios nas áreas indicadas (arrastando ou clicando)</li>"
        "<li>Clique no botão \"Unificar Relatórios\" para processar os dados</li>"
        "<li>Explore os resultados nas abas \"Resultados Gerais\" e \"Categorias de Usuários\"</li>"
        "<li>Exporte os dados unificados para um arquivo JSON, se desejar</li>"
        "</ol>"

        "<p><strong>Importante:</strong> Por padrão, apenas relatórios gerados hoje serão aceitos. "
        "Para processar relatórios de outras datas, desmarque a opção 'Verificar se os arquivos são do dia atual'.</p>"
    )

def get_categories_html(categories_data):
    """
    Gera o HTML para exibição das categorias de usuários.
    """
    html = """
    <div style='font-family: Arial; font-size: 12px;'>
        <h2 style='color: #2c3e50;'>Categorias de Usuários</h2>
    """

    for category in categories_data:
        html += f"""
        <div style='margin-bottom: 20px; border: 1px solid {category['header_color']}; border-radius: 5px; overflow: hidden;'>
            <div style='background-color: {category['header_color']}; color: white; padding: 10px;'>
                <h3 style='margin: 0;'>{category['icon']} {category['name']}</h3>
                <p style='margin: 5px 0 0 0; font-size: 11px;'>{category['description']}</p>
            </div>
            <div style='padding: 10px; background-color: {category['stripe_color']};'>
                <p style='margin: 0;'><strong>Total de usuários:</strong> {len(category['users'])}</p>
            </div>
            <div style='padding: 10px;'>
                <table style='width: 100%; border-collapse: collapse;'>
                    <thead>
                        <tr style='background-color: #f5f5f5;'>
                            <th style='padding: 8px; text-align: left; border-bottom: 1px solid #ddd;'>Código</th>
                            <th style='padding: 8px; text-align: left; border-bottom: 1px solid #ddd;'>Nome</th>
                            <th style='padding: 8px; text-align: right; border-bottom: 1px solid #ddd;'>Multa Total</th>
                            <th style='padding: 8px; text-align: right; border-bottom: 1px solid #ddd;'>Pendências</th>
                            <th style='padding: 8px; text-align: left; border-bottom: 1px solid #ddd;'>Email</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for user in category['users']:
            html += f"""
                        <tr>
                            <td style='padding: 8px; border-bottom: 1px solid #eee;'>{user['code']}</td>
                            <td style='padding: 8px; border-bottom: 1px solid #eee;'>{user['name']}</td>
                            <td style='padding: 8px; border-bottom: 1px solid #eee; text-align: right;'>R$ {user['fine']:.2f}</td>
                            <td style='padding: 8px; border-bottom: 1px solid #eee; text-align: right;'>{user['pending']}</td>
                            <td style='padding: 8px; border-bottom: 1px solid #eee;'>{user['email']}</td>
                        </tr>
            """

        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """

    html += """
    </div>
    """

    return html