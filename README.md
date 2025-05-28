# Sistema de Cobrança da Biblioteca

Este sistema gerencia as cobranças de multas e pendências da biblioteca, permitindo a unificação de relatórios, visualização de estatísticas e envio de notificações por e-mail, tudo em uma interface gráfica moderna baseada em PyQt6.

## Estrutura Modular

O projeto segue uma arquitetura modular, facilitando a manutenção e evolução do código:

### Organização dos Módulos

- **modules/**
  - **tabs/**: Classes para cada aba da interface
    - `base_tab.py`: Classe base abstrata para todas as abas
    - `import_tab.py`: Aba de importação de arquivos Excel
    - `results_tab.py`: Aba de visualização de resultados da unificação
    - `template_tab.py`: Aba de configuração de templates de e-mail
    - `email_tab.py`: Aba de envio de emails com templates personalizados
    - `export_tab.py`: (opcional) Exportação de dados
    - `summary_tab.py`: (opcional) Resumo dos dados
    - `__init__.py`: Exportação das classes e configuração das abas
  - `components.py`: Componentes de UI reutilizáveis
  - `config_manager.py`: Gerenciador de configurações
  - `data_processor.py`: Processamento de dados
  - `gui_interface.py`: Interface principal
  - `read_excel.py`: Funções de leitura e processamento de Excel
  - `styles_fix.py`: Estilos e temas da interface

### Funcionalidades Principais

1. **Importação de Dados**
   - Suporte para arquivos Excel (.xlsx, .xls)
   - Validação de dados e verificação de data
   - Unificação de relatórios de multas e pendências

2. **Visualização de Resultados**
   - Tabelas e cards interativos
   - Estatísticas em tempo real
   - Resumo dos dados processados

3. **Gerenciamento de Templates**
   - Criação e edição de templates de e-mail
   - Personalização de mensagens com variáveis dinâmicas
   - Visualização em Markdown

4. **Envio de E-mails**
   - Envio em massa com templates personalizados
   - Visualização de prévia antes do envio

5. **Exportação e Resumo** (se ativado)
   - Exportação dos dados unificados
   - Resumo estatístico dos dados

### Padrões de Projeto Utilizados

- **Herança**: Todas as abas herdam de uma classe base comum
- **Signals e Slots**: Comunicação entre componentes usando o mecanismo de sinais do PyQt6
- **Injeção de Dependência**: As classes recebem suas dependências no construtor
- **Responsabilidade Única**: Cada classe tem uma responsabilidade bem definida

## Benefícios da Modularização

1. **Manutenibilidade**: Código mais organizado e fácil de entender
2. **Testabilidade**: Classes isoladas podem ser testadas individualmente
3. **Extensibilidade**: Novas funcionalidades podem ser adicionadas com menos impacto
4. **Reusabilidade**: Componentes podem ser reutilizados em diferentes partes da aplicação

## Como Executar

Execute o sistema com o comando:

```bash
python main.py
```

## Requisitos

- Python 3.8+
- PyQt6
- pandas
- markdown
- openpyxl

Instale as dependências com:

```bash
pip install -r requirements.txt
```

## Desenvolvimento

Para adicionar uma nova aba à interface:

1. Crie uma nova classe que herde de `BaseTab` em `modules/tabs/`
2. Implemente o método `setup_ui()`
3. Adicione a nova classe ao `__init__.py` do pacote tabs
4. Configure os sinais necessários no método `setup_tabs()`
5. Atualize a interface principal para usar a nova classe