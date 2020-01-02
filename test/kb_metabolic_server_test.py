# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from kb_metabolic.kb_metabolicImpl import kb_metabolic
from kb_metabolic.kb_metabolicServer import MethodContext
from kb_metabolic.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace
from installed_clients.kb_gtdbtkClient import kb_gtdbtk


class kb_metabolicTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = os.environ.get('KB_AUTH_TOKEN', None)
        config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_metabolic'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_metabolic',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = kb_metabolic(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace({'workspace': cls.wsName})  # noqa

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    #NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def test_kb_metabolic(self):
        print("START test_kb_metabolic\n")
        ret = self.serviceImpl.run_kb_metabolic(self.ctx, {'workspace_name': self.wsName,
                                                             'inputObjectRef': '30870/32/3',
                                                            #  'reads_list' : ['30870/211/1'], # single end
                                                             'reads_list' : ['30870/213/1'], # interleaved
                                                             'kegg_module_cutoff': '0.75',
                                                             'prodigal_method': 'meta'})
