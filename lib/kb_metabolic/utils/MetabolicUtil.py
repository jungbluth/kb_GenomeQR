import os
import subprocess
import logging

from installed_clients.ReadsUtilsClient import ReadsUtils

class MetabolicUtil():
    '''
    Utilities for running METABOLIC
    '''

    def __init__(self, config, callback_url, workspace_id, cpus):
        self.shared_folder = config['scratch']
        self.callback_url = callback_url
        self.cpus = cpus
        self.ru = ReadsUtils(self.callback_url)

        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)


    def stage_reads_list_file(self, reads_list):
        """
        stage_reads_list_file: download fastq file associated to reads to scratch area
                          and return result_file_path
        """

        logging.info('Processing reads object list: {}'.format(reads_list))

        result_file_path = []
        read_type = []

        # getting from workspace and writing to scratch. The 'reads' dictionary now has file paths to scratch.
        reads = self.ru.download_reads({'read_libraries': reads_list, 'interleaved': None})['files']

        # reads_list is the list of file paths on workspace? (i.e. 12804/1/1).
        # "reads" is the hash of hashes where key is "12804/1/1" or in this case, read_obj and
        # "files" is the secondary key. The tertiary keys are "fwd" and "rev", as well as others.
        for read_obj in reads_list:
            files = reads[read_obj]['files']    # 'files' is dictionary where 'fwd' is key of file path on scratch.
            result_file_path.append(files['fwd'])
            read_type.append(files['type'])
            if 'rev' in files and files['rev'] is not None:
                result_file_path.append(files['rev'])

        return result_file_path, read_type


    def _run_command(self, command):
        """
        _run_command: run command and print result
        """
        os.chdir(self.shared_folder)
        logging.info('Start executing command:\n{}'.format(command))
        logging.info('Command is running from:\n{}'.format(self.shared_folder))
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, stderr = pipe.communicate()
        exitCode = pipe.returncode

        if (exitCode == 0):
            logging.info('Executed command:\n{}\n'.format(command) +
                'Exit Code: {}\n'.format(exitCode))
        else:
            error_msg = 'Error running command:\n{}\n'.format(command)
            error_msg += 'Exit Code: {}\nOutput:\n{}\nStderr:\n{}'.format(exitCode, output, stderr)
            raise ValueError(error_msg)
            sys.exit(1)
        return (output, stderr)


    def deinterlace_raw_reads(self, fastq):
        fastq_forward = fastq.split('.fastq')[0] + "_forward.fastq"
        fastq_reverse = fastq.split('.fastq')[0] + "_reverse.fastq"
        command = 'reformat.sh in={} out1={} out2={} overwrite=true'.format(fastq, fastq_forward, fastq_reverse)
        self._run_command(command)
        return (fastq_forward, fastq_reverse)


    def make_metabolic_reads_file_input(self, params):
        """
            This function runs the selected read mapper and creates the
            sorted and indexed bam files from sam files using samtools.
        """

        reads_list = params['reads_list']

        (read_scratch_path, read_type) = self.stage_reads_list_file(reads_list)

        omic_reads_parameter_file = os.path.abspath(self.shared_folder) + '/omic_reads_parameters.txt'
        with open(omic_reads_parameter_file, 'w+') as f:
            f.write("#Reads pair name with complete pathway: \n")

            for i in range(len(read_scratch_path)):
                fastq = read_scratch_path[i]
                fastq_type = read_type[i]

                if fastq_type == 'interleaved':  # make sure working - needs tests
                    logging.info("Running interleaved read mapping mode")
                    (fastq_forward, fastq_reverse) = self.deinterlace_raw_reads(fastq)
                    f.write(fastq_forward + ',' + fastq_reverse)
                else:  # running read mapping in single-end mode
                    logging.info("Running unpaired read mapping mode")
                    f.write(fastq)
        return omic_reads_parameter_file


    def run_metabolic_without_reads(self, params):
        '''
        Run the METABOLIC-G workflow (not using raw reads)
        '''
        out_dir = os.path.join(self.shared_folder, "output")
        metabolic_cmd = " ".join(["perl", "/kb/module/bin/METABOLIC/METABOLIC-G.pl",
                                  "-in-gn", self.shared_folder,
                                  "-t", str(self.cpus),
                                  "-m-cutoff", str(params['kegg_module_cutoff']),
                                  "-p", params['prodigal_method'],
                                  "-o", out_dir,
                                  "-m", "/data/METABOLIC"])
        logging.info("Starting Command:\n" + metabolic_cmd)
        output = subprocess.check_output(metabolic_cmd, shell=True).decode('utf-8')
        logging.info(output)

        # self._process_output_files(out_dir)
        return output

    def run_metabolic_with_reads(self, params):
        '''
        Run the METABOLIC-C workflow (using raw reads)
        '''
        out_dir = os.path.join(self.shared_folder, "output")
        omic_reads_parameter_file = self.make_metabolic_reads_file_input(params)
        metabolic_cmd = " ".join(["perl", "/kb/module/bin/METABOLIC/METABOLIC-C.pl",
                                  "-in-gn", self.shared_folder,
                                  "-t", str(self.cpus),
                                  "-m-cutoff", params['kegg_module_cutoff'],
                                  "-p", params['prodigal_method'],
                                  "-o", out_dir,
                                  "-m", "/data/METABOLIC",
                                  "-r", omic_reads_parameter_file])
        logging.info("Starting Command:\n" + metabolic_cmd)
        output = subprocess.check_output(metabolic_cmd, shell=True).decode('utf-8')
        logging.info(output)

        # self._process_output_files(out_dir)
        return output
    #
    # def _process_output_files(self, out_dir):
    #
    #     for path in (os.path.join(out_dir, 'gtdbtk.ar122.summary.tsv'),
    #                  os.path.join(out_dir, 'gtdbtk.bac120.summary.tsv'),
    #                  os.path.join(out_dir, 'gtdbtk.bac120.markers_summary.tsv'),
    #                  os.path.join(out_dir, 'gtdbtk.ar122.markers_summary.tsv'),
    #                  os.path.join(out_dir, 'gtdbtk.filtered.tsv')):
    #         try:
    #             summary_df = pd.read_csv(path, sep='\t', encoding='utf-8')
    #             outfile = path + '.json'
    #             summary_json = '{"data": ' + summary_df.to_json(orient='records') + '}'
    #             with open(outfile, 'w') as out:
    #                 out.write(summary_json)
    #         except Exception as exc:
    #             logging.info(exc)
    #
    #     return
