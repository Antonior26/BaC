import glob
import json
import logging
import os
from app.ORF import ORF

from bac_tasks.pipelines.vfdb_filter import Filter

level = logging.WARNING
logger = logging.getLogger(__name__)
logger.setLevel(level)
formatter = logging.Formatter('%(levelname)s %(asctime)s : %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class VFBDRunner(object):

    def __init__(self, db_folder, input_type='contig', input_sequence=None, threads=32, output_file=None, loose=False,
                 clean=True, data='na', aligner='diamond', low_quality=False, debug=False):

        o_f_path, o_f_name = os.path.split(os.path.abspath(output_file))
        self.input_type = input_type.lower()
        self.input_sequence = os.path.abspath(input_sequence)
        self.threads = threads
        self.num_sequences = 1
        self.output_file = os.path.abspath(output_file)
        self.loose = loose
        self.clean = clean
        self.data = data
        self.aligner = aligner.lower()
        self.low_quality = low_quality

        self.local_database = True
        self.db = db_folder
        self.dp = db_folder

        self.working_directory = o_f_path
        self.blast_results_xml_file = ''
        self.debug = debug

        if self.debug:
            logger.setLevel(10)

    def __set_xml_filepath(self, fp):
        """Sets blast xml filepath."""
        self.blast_results_xml_file = fp

    def run(self):
        """Runs RGI."""
        self.run_blast()
        self.filter_process()

    def clean_files(self):
        """Cleans temporary files."""
        if self.clean == True:
            basename_output_file = os.path.splitext(os.path.basename(self.output_file))[0]
            logger.info("Cleaning up temporary files...{}".format(basename_output_file))
            # clean working_directory
            self.clean_directory(self.working_directory, basename_output_file)
            d_name, f_name = os.path.split(self.output_file)
            # clean destination_directory
            self.clean_directory(d_name, basename_output_file)
        else:
            logger.info("Clean up skipped.")

    def clean_directory(self, directory, basename_output_file):
        """Cleans files in directory."""
        logger.info(directory)
        files = glob.glob(os.path.join(directory, "*"))
        for f in files:
            if os.path.basename(self.input_sequence) + ".temp" in f and os.path.isfile(f):
                self.remove_file(f)

    def remove_file(self, f):
        """Removes file."""
        if os.path.exists(f):
            logger.info("Removed file: {}".format(f))
            os.remove(f)
        else:
            logger.warning("Missing file: {}".format(f))

    def run_blast(self):
        """Runs blast."""
        if self.input_type == "protein":
            self.process_protein()
        elif self.input_type == "contig":
            self.process_contig()
        elif self.input_type == "read":
            self.process_read()
            # logger.debug("TODO:: add read functions")
            exit("")
        else:
            logger.error("Invalid input_type: {} ".format(self.input_type))
            exit()

    def set_xml_filepath(self, fp):
        """Sets blast xml filepath."""
        logger.info("set blast xml file: [{}]".format(fp))
        self.blast_results_xml_file = fp

    def process_protein(self):
        """Process protein sequence(s)."""
        file_name = os.path.basename(self.input_sequence)
        xml_file = os.path.join(self.working_directory, "{}.temp.blastRes.xml".format(file_name))

        if self.aligner == "diamond":
            diamond_obj = Diamond(self.input_sequence, self.db, xml_file, local_database=self.local_database,
                                  num_threads=self.threads)
            diamond_obj.run()
        else:
            blast_obj = Blast(self.input_sequence, self.db, xml_file, local_database=self.local_database,
                              num_threads=self.threads)
            blast_obj.run()

        self.set_xml_filepath(xml_file)

    def process_contig(self):
        """Process nuclotide sequence(s)."""
        file_name = os.path.basename(self.input_sequence)
        orf_obj = ORF(input_file=self.input_sequence, clean=self.clean, working_directory=self.working_directory,
                      low_quality=self.low_quality)
        orf_obj.contig_to_orf()
        contig_fsa_file = os.path.join(self.working_directory, "{}.temp.contig.fsa".format(file_name))
        blast_results_xml_file = os.path.join(self.working_directory,
                                              "{}.temp.contig.fsa.blastRes.xml".format(file_name))

        try:
            if os.stat(contig_fsa_file).st_size > 0:
                logger.info("work with file {}".format(contig_fsa_file))
                if self.aligner == "diamond":
                    diamond_obj = Diamond(contig_fsa_file, db_path=self.db, local_database=self.local_database, num_threads=self.threads)
                    diamond_obj.run()
                else:
                    blast_obj = Blast(contig_fsa_file, db_path=self.db, local_database=self.local_database, num_threads=self.threads)
                    blast_obj.run()
                self.set_xml_filepath(blast_results_xml_file)
            else:
                self.write_stub_output_file()
                logger.error("no open reading frames (orfs) found.")
        except Exception as e:
            self.write_stub_output_file()
            logger.exception("failed to write orf file")
        else:
            # logger.info("success procession orf file")
            pass

    def write_stub_output_file(self):
        # write empty output file if there are no open reading frames
        with open(os.path.join(self.output_file), 'w') as fout:
            fout.write(json.dumps({}))

    def process_read(self):
        """Process fastq or reads sequence(s)."""
        logger.info("process read")

    # @profile
    def filter_process(self):
        logger.info("run filter")
        """Filter each detection models and predict resistome(s)."""
        filter_obj = Filter(self.input_type, self.loose, self.input_sequence, self.blast_results_xml_file,
                            os.path.join(self.dp, "VFDB.json"), os.path.basename(self.input_sequence), self.output_file,
                            self)
        filter_obj.run()


class Blast(object):
    """Class to create Blast object and align for protein and translated DNA searches."""
    def __init__(self,input_file, db_path, output_file=None, program = 'blastp', num_threads=32, local_database=False ):
        """Creates Blast object for running NCBI BLAST algorithm."""
        self.input_file = input_file
        if output_file == None:
            f_path, f_name = os.path.split(input_file)
            self.output_file = os.path.join(f_path,"{}.blastRes.xml".format(f_name))
        else:
            self.output_file = output_file
        self.local_database = local_database
        self.db = db_path
        self.program = program
        self.num_threads = num_threads
        self.outfmt = 5

    def __repr__(self):
        """Returns Blast class full object."""
        return "Blast({}".format(self.__dict__)

    def run(self):
        """Runs BLAST algorithm."""
        logger.info("run blast")
        os.system('{program} -query {input} -db {path} \
					-num_threads {num_threads} -outfmt {outfmt} -out {output_file}' \
            .format(
            program=self.program,
            num_threads=self.num_threads,
            outfmt=self.outfmt,
            input=self.input_file,
            path=os.path.join(self.db,"protein.db"),
            output_file=self.output_file
        )
        )

    def run_custom(self, db ):
        """Runs DIAMOND algorithm."""
        # logger.info("run diamond")
        os.system('{program} -query {input} -db {db} -num_threads {num_threads} \
					-outfmt {outfmt} -out {output_file} -perc_identity {perc_identity} \
					-strand {strand}' \
            .format(
            program=self.program,
            input=self.input_file,
            db=db,
            num_threads=self.num_threads,
            outfmt=self.outfmt,
            output_file=self.output_file,
            perc_identity=95.0,
            strand="both"
        )
        )
        logger.info("done running {} -> {}".format(self.program, db))





class Diamond(object):
    """Class to create Diamond object and align for protein and translated DNA searches."""

    def __init__(self, input_file, db_path, output_file=None, program='blastp', num_threads=32, local_database=False):
        """Creates Diamond object for running DIAMOND algorithm."""
        self.input_file = input_file
        if output_file == None:
            f_path, f_name = os.path.split(input_file)
            self.output_file = os.path.join(f_path, "{}.blastRes.xml".format(f_name))
        else:
            self.output_file = output_file

        self.local_database = local_database
        self.db = db_path

        self.program = program
        self.num_threads = num_threads
        self.index_chunks = 1
        self.block_size = 1
        self.outfmt = 5

    def __repr__(self):
        """Returns Diamond class full object."""
        return "Diamond({}".format(self.__dict__)

    def run(self):
        """Runs DIAMOND algorithm."""
        # logger.info("run diamond")
        os.system('diamond {program} --in {in_ref} --db {db} \
                    --query {input} --outfmt {outfmt} --out {output_file}  \
                    --threads {num_threads}  --index-chunks {index_chunks} \
                    --block-size {block_size}  \
                    --salltitles  --quiet --more-sensitive'.format(
            program=self.program,
            in_ref=os.path.join(self.db, "proteindb.fsa"),
            db=os.path.join(self.db, "protein.db"),
            input=self.input_file,
            output_file=self.output_file,
            num_threads=self.num_threads,
            index_chunks=self.index_chunks,
            block_size=self.block_size,
            outfmt=self.outfmt
        )
        )


r = VFBDRunner(db_folder='/home/aruedamartin/PycharmAntonio/BaC/reference/VFDBlocal/localDB',
               input_sequence='/home/aruedamartin/Desktop/assemblies/105_assembly-6.500.short_id.fa',
               output_file='/home/aruedamartin/tmp/test_vf/', clean=False, loose=True, aligner='blast'
               )

r.run()
