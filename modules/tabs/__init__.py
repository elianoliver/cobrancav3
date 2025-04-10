"""
Pacote de módulos para abas da interface gráfica.

Este pacote contém as classes para cada aba da aplicação,
facilitando a modularização e manutenção do código.

Estrutura do pacote:
- base_tab.py: Classe base abstrata que todas as abas herdam
- import_tab.py: Aba de importação de arquivos Excel
- results_tab.py: Aba de exibição de resultados da unificação
- summary_tab.py: Aba de resumo dos dados
- template_tab.py: Aba de configuração de templates de e-mail
- export_tab.py: Aba de exportação de dados em diversos formatos

Cada aba implementa sua própria interface gráfica e lógica de
negócios específica, enquanto herda funcionalidades comuns da classe
BaseTab. A comunicação entre as abas é feita através de sinais
(pyqtSignal) que são conectados na interface principal.

O padrão de modularização adotado segue o princípio de
responsabilidade única, onde cada classe é responsável por uma
parte específica da interface e suas funcionalidades.
"""

from modules.tabs.base_tab import BaseTab
from modules.tabs.import_tab import ImportTab
from modules.tabs.results_tab import ResultsTab
from modules.tabs.summary_tab import SummaryTab
from modules.tabs.template_tab import TemplateTab
from modules.tabs.export_tab import ExportTab

__all__ = [
    'BaseTab',
    'ImportTab',
    'ResultsTab',
    'SummaryTab',
    'TemplateTab',
    'ExportTab',
]