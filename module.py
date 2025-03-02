#!/usr/bin/python3
# coding=utf-8

#   Copyright 2021 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Module """
import json
from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import module

from tools import VaultClient, worker_client  # pylint: disable=E0611,E0401

from .models.integration_pd import IntegrationModel


CAPATIBILITIES_MAP = {
    'completion':
        ['gpt-3.5-turbo-instruct', 'babbage-002', 'davinci-002'],
    'chat_completion':
        ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-4-0613', 'gpt-4-32k', 'gpt-4-32k-0613', 'gpt-3.5-turbo',
         'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-16k-0613'],
    'embeddings':
        ['text-embedding-ada-002']
}

TOKEN_LIMITS = {
    'gpt-3.5-turbo-instruct': 4097,
    'babbage-002': 16384,
    'davinci-002': 16384,
    'gpt-4': 8192,
    'gpt-4-0613': 8192,
    'gpt-4-32k': 32768,
    'gpt-4-32k-0613': 32768,
    'gpt-3.5-turbo': 4097,
    'gpt-3.5-turbo-0613': 4097,
    'gpt-3.5-turbo-16k': 16385,
    'gpt-3.5-turbo-16k-0613': 16385,
    'text-embedding-ada-002': None,
    'text-davinci-003': 4097,
    'text-davinci-002': 4097,
    'code-davinci-002': 8001
}


class Module(module.ModuleModel):
    """ Task module """

    def __init__(self, context, descriptor):
        self.context = context
        self.descriptor = descriptor

    def init(self):
        """ Init module """
        log.info('Initializing AI module')
        SECTION_NAME = 'ai'
        #
        self.descriptor.init_all()
        #
        self.context.rpc_manager.call.integrations_register_section(
            name=SECTION_NAME,
            integration_description='Manage ai integrations',
        )
        self.context.rpc_manager.call.integrations_register(
            name=self.descriptor.name,
            section=SECTION_NAME,
            settings_model=IntegrationModel,
        )
        #
        vault_client = VaultClient()
        secrets = vault_client.get_all_secrets()
        if 'open_ai_capatibilities_map' not in secrets:
            secrets['open_ai_capatibilities_map'] = json.dumps(CAPATIBILITIES_MAP)
            vault_client.set_secrets(secrets)
        if 'open_ai_token_limits' not in secrets:
            secrets['open_ai_token_limits'] = json.dumps(TOKEN_LIMITS)
            vault_client.set_secrets(secrets)
        #
        worker_client.register_integration(
            integration_name=self.descriptor.name,
            #
            ai_check_settings_callback=self.ai_check_settings,
            ai_get_models_callback=self.ai_get_models,
            ai_count_tokens_callback=self.count_tokens,
            #
            llm_invoke_callback=self.llm_invoke,
            llm_stream_callback=self.llm_stream,
            #
            chat_model_invoke_callback=self.chat_model_invoke,
            chat_model_stream_callback=self.chat_model_stream,
            #
            embed_documents_callback=self.embed_documents,
            embed_query_callback=self.embed_query,
            #
            indexer_config_callback=self.indexer_config,
        )

    def deinit(self):
        """ De-init module """
        log.info('De-initializing')
        #
        self.descriptor.deinit_all()
