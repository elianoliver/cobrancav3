# Sistema de Cobrança da Biblioteca

Este sistema gerencia as cobranças de multas e pendências da biblioteca, permitindo a unificação de relatórios, visualização de estatísticas, e envio de notificações.

## Estrutura Modular

O projeto foi reestruturado para seguir uma arquitetura modular, facilitando a manutenção e evolução do código:

### Organização dos Módulos

- **modules/**
  - **tabs/**: Classes para cada aba da interface
    - `base_tab.py`: Classe base abstrata para todas as abas
    - `import_tab.py`: Aba de importação de arquivos
    - `results_tab.py`: Aba de visualização de resultados
    - `summary_tab.py`: Aba de resumo estatístico
    - `__init__.py`: Exportação das classes e documentação
  - `components.py`: Componentes de UI reutilizáveis
  - `config_manager.py`: Gerenciador de configurações
  - `data_processor.py`: Processamento de dados
  - `gui_interface.py`: Interface principal
  - `read_excel.py`: Funções de leitura e processamento de Excel
  - `styles_fix.py`: Estilos e temas da interface

### Padrões de Projeto Utilizados

- **Herança**: Todas as abas herdam de uma classe base comum
- **Signals e Slots**: Comunicação entre componentes usando o mecanismo de sinais do PyQt
- **Injeção de Dependência**: As classes recebem suas dependências no construtor
- **Responsabilidade Única**: Cada classe tem uma responsabilidade bem definida

## Benefícios da Modularização

1. **Manutenibilidade**: Código mais organizado e fácil de entender
2. **Testabilidade**: Classes isoladas podem ser testadas individualmente
3. **Extensibilidade**: Novas funcionalidades podem ser adicionadas com menos impacto
4. **Reusabilidade**: Componentes podem ser reutilizados em diferentes partes da aplicação

## Como Executar

```bash
python -m modules.gui_interface
```

## Requisitos

- Python 3.8+
- PyQt6
- pandas
- openpyxl

## Desenvolvimento

Para adicionar uma nova aba à interface:

1. Crie uma nova classe que herde de `BaseTab`
2. Implemente o método `setup_ui()`
3. Adicione a nova classe ao `__init__.py` do pacote tabs
4. Atualize a interface principal para usar a nova classe