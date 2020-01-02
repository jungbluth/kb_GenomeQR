# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from kb_metabolic.utils.misc_utils import load_fastas
from kb_metabolic.utils.misc_utils import rename_input_file_suffixes
from kb_metabolic.utils.misc_utils import create_html_report

from kb_metabolic.utils.MetabolicUtil import MetabolicUtil

from installed_clients.kb_gtdbtkClient import kb_gtdbtk
from installed_clients.baseclient import ServerError


#END_HEADER


class kb_metabolic:
    '''
    Module Name:
    kb_metabolic

    Module Description:
    A KBase module: kb_metabolic
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found

    # def __init__(self, config):
    #     #BEGIN_CONSTRUCTOR
    #     self.callback_url = os.environ['SDK_CALLBACK_URL']
    #     self.shared_folder = config['scratch']
    #     logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
    #                         level=logging.INFO)
    #     #END_CONSTRUCTOR
    #     pass

    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        self.config = config
        self.config['callback_url'] = self.callback_url
        self.cpus = 2  # bigmem 32 cpus & 90,000MB RAM

        #END_CONSTRUCTOR
        pass

    def run_kb_metabolic(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_kb_metabolic

        # TODO: some parameter checking
        try:
            ref = params.get('inputObjectRef')
        except KeyError:
            print("Must provide a ws reference to object with sequences")

        try:
            workspace_id = params.get('workspace_id')
        except KeyError:
            print("Must provide a workspace id")

        # get the fasta file from the input ref
        # TODO: handle sets
        logging.info("Get Genome Seqs\n")
        fasta_paths = load_fastas(self.config, self.shared_folder, ref)
        print(fasta_paths)

        logging.info("Rename Genome File Suffixes\n")
        rename_input_file_suffixes(self.shared_folder)


        print('\n\n\n {}'.format(os.path.abspath(self.shared_folder)))
        os.makedirs(os.path.abspath(self.shared_folder) + '/output')

        print('Running GTDBtk')
        gtdbtk = kb_gtdbtk(self.callback_url)
        try:
            gtdbtkret = gtdbtk.run_kb_gtdbtk({'inputObjectRef': '30870/32/3'})

        except ServerError as gtdbtke:
            # not really any way to test this, all inputs have been checked earlier and should be
            # ok
            print('Logging exception from running GTDBtk')
            print(str(gtdbtke))
            # TODO delete shock node
            raise

        logging.info("Run METABOLIC\n")
        metabolic = MetabolicUtil(self.config, self.callback_url, workspace_id, self.cpus)

        print('\n\nreads_list is: {}'.format(params.get('reads_list')))
        if params.get('reads_list') is None:
          #results = metabolic.run_metabolic_without_reads(params)
          print("None")
        else:
          print("NotNone")
          results = metabolic.run_metabolic_with_reads(params)

        logging.info(results)
        output = create_html_report(self.callback_url, self.shared_folder, params['workspace_name'])

        #END run_kb_metabolic

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_kb_metabolic return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
