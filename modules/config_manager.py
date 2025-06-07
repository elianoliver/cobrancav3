"""
Gerenciador de configurações da aplicação.

Este módulo contém a classe ConfigManager responsável por carregar,
salvar e gerenciar as configurações da aplicação.
"""

import os
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
            'ultimo_diretorio': '',
            # Configurações de disparo de e-mails
            'email_remetente': '',              # Endereço de e-mail do remetente
            'email_senha_app': '',              # Senha de app do remetente
            'email_destinatario_padrao': '',    # Destinatário padrão (opcional)
            'email_assunto_padrao': ''          # Assunto padrão do e-mail (opcional)
        }
        self._save_config(default_config)
        return default_config