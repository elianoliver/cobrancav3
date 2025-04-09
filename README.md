# Sistema de Cobrança - Biblioteca IFC

Sistema para processamento de relatórios de multas e pendências da biblioteca, com geração de templates de notificação.

## Melhorias de Estilização

O sistema foi atualizado para utilizar recursos nativos de estilização do PyQt6, proporcionando:

### 1. Abordagem Orientada a Objetos para Estilos

- `AppColors`: Classe centralizada com todas as cores do sistema
- `StyleManager`: Gerencia a aplicação de estilos usando APIs nativas do Qt

### 2. Benefícios da Nova Abordagem

- **Menos CSS inline**: Redução significativa de código CSS personalizado
- **Uso de QPalette**: Aproveitamento do sistema nativo de paletas
- **Estilo Fusion**: Melhor consistência entre plataformas
- **Separação de Conceitos**: Classes específicas para cada elemento de UI
- **Manutenção Simplificada**: Modificações de estilo centralizadas

### 3. Elementos Nativos Utilizados

- `QPalette`: Para definir cores a nível de aplicação e componentes
- `QFont`: Para controle tipográfico consistente
- `QStyleFactory`: Para aplicar o estilo Fusion multiplataforma
- `QColor`: Para manipulação programática de cores

### 4. Recursos Visuais Aprimorados

- Cores organizadas por categoria semântica (primária, alerta, sucesso, etc.)
- Tipografia consistente em toda a aplicação
- Estilos específicos para tipos de componentes (botões, frames, etc.)
- Melhor feedback visual para interações do usuário

## Como Executar

```bash
python -m modules.gui_interface
```