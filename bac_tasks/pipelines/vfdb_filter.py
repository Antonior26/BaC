import json
import logging
import os
from Bio import SeqIO
from Bio.Alphabet import DNAAlphabet
from app.Base import BaseModel
from app.Blast import Blast
from app.Database import Database
from app.ConvertRGIJsonToTSV import ConvertJsonToTSV
from Bio.Blast import NCBIXML
import hashlib
import multiprocessing
from Bio.Seq import Seq

level = logging.WARNING
logger = logging.getLogger(__name__)
logger.setLevel(level)
formatter = logging.Formatter('%(levelname)s %(asctime)s : %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
generic_dna = DNAAlphabet()

class Filter(BaseModel):
    """This class takes in blast xml file and card.json file and producess perfect strict paradigm for RGI """

    def __init__(self, input_type, loose, input_sequence, xml_file, card_json, input_file, output_file, rgi_obj=None):
        self.input_type = input_type
        self.xml_file = xml_file
        self.card_json = card_json
        self.input_filename = input_file
        self.input_sequence = input_sequence
        self.loose = loose
        self.blast_results = {}
        self.rgi_obj = rgi_obj
        self.working_directory = rgi_obj.working_directory

        if output_file == None:
            f_path, f_name = os.path.split(input_file)
            self.output_file = os.path.join(f_path, "{}.Report.json".format(f_name))
        else:
            self.output_file = output_file

    def __repr__(self):
        """Returns Filter class full object."""
        return "Filter({}".format(self.__dict__)

    def worker(self, model_type):
        logger.info("{}_worker started...".format(model_type))
        # results = {}
        try:
            if model_type == "homolog":
                obj = Homolog(self.input_type, self.rgi_obj.db, self.loose, self.input_sequence, self.xml_file, self.working_directory,
                              self.rgi_obj.local_database)
            results = obj.run()
            logger.info("save {} results...".format(model_type))
            file_name = os.path.basename(self.input_sequence)
            with open(os.path.join(self.working_directory, "{}.temp.{}.json".format(file_name, model_type)),
                      'w') as fout:
                fout.write(json.dumps(results))

        except Exception as e:
            logger.warning("Exception: {} -> {} -> model_type: {}".format(type(e), e, model_type))

    def async_func(self):
        p = multiprocessing.Process(target=self.worker, args=("homolog",))
        logger.info("{} -> {}".format(p.pid, p.name))
        p.start()

    def prepare_output(self):
        """
        Read all json into one json results file
        """
        logger.info("prepare output(s) for input: {}".format(self.input_sequence))
        file_name = os.path.basename(self.input_sequence)
        obj = ConvertJsonToTSV(self.output_file,
                               os.path.join(self.working_directory, "{}.temp.{}.json".format(file_name, "homolog"))

                               )
        # combine 3 json files
        obj.combine_jsons()
        # write tsv
        obj.run()

    def cleanup(self):
        self.rgi_obj.clean_files()

    def process_xml_file(self):
        """ This function is used to process blast xml file """
        model_thread = multiprocessing.Process(target=self.async_func, args=())
        model_thread.start()
        model_thread.join()
        prepare_output_thread = multiprocessing.Process(target=self.prepare_output, args=())
        prepare_output_thread.start()
        prepare_output_thread.join()
        cleanup_thread = multiprocessing.Process(target=self.cleanup, args=())
        cleanup_thread.start()


    def create_db_query(self):
        logger.info("create_db_query")
        # make_custom_db(self, in_file, out_file, db_type="diamond")
        in_file = self.input_sequence
        f_path, f_name = os.path.split(self.input_sequence)
        out_file = os.path.join(self.working_directory, "{}.db".format(f_name))
        xml_file = os.path.join(self.working_directory, "{}.blastRes.rrna.xml".format(f_name))
        logger.info("DB from user query")
        db_obj = Database(self.rgi_obj.local_database)
        db_obj.make_custom_db(in_file, out_file)
        self.blast_reference_to_db_query(out_file, xml_file)
        return out_file, xml_file

    def blast_reference_to_db_query(self, db, xml_file):
        logger.info("blast_reference_to_db_query")
        # blast all rrna db against query db
        rrna_db_fasta = os.path.join(self.rgi_obj.db, "rnadb.fsa")
        blast_obj = Blast(rrna_db_fasta, program='blastn', output_file=xml_file,
                          local_database=self.rgi_obj.local_database)
        blast_obj.run_custom(db)

    def format_fasta(self):
        f_path, f_name = os.path.split(self.input_sequence)
        temp_file = os.path.join(self.working_directory, "{}.temp".format(f_name))
        with open(temp_file, 'w') as fout:
            for record in SeqIO.parse(self.input_sequence, 'fasta'):
                header = record.id
                seq = record.seq
                fout.write(">{}\n{}\n".format(header, seq))
        self.input_sequence = temp_file

    def encode_header(self, name):
        return hashlib.md5(name.encode('utf-8')).hexdigest()


    def run(self):
        if (os.path.exists(self.xml_file)):
            self.process_xml_file()
        else:
            logger.error(
                "missing blast xml file({}). Please check if input_type: '{}' correspond with input file: '{}' or use '--low_quality' flag for short contigs to predicts partial genes." \
                    .format(self.xml_file, self.input_type, self.input_sequence))



class Homolog(BaseModel):
    """Class for homology searches."""

    def __init__(self, input_type, db_path, loose, input_sequence, xml_file, working_directory, local_database=False):
        self.input_type = input_type
        self.loose = loose
        self.input_sequence = input_sequence
        self.xml_file = xml_file
        self.output = {}
        self.working_directory = working_directory

        self.local_database = local_database

        self.db = db_path
        self.data = db_path

    def __repr__(self):
        """Returns Homolog class full object."""
        return "Homolog({}".format(self.__dict__)

    def run(self):
        """Runs homolog search."""
        blastResults = {}

        predicted_genes_dict = {}
        submitted_proteins_dict = {}

        if self.input_type == "contig":
            predicted_genes_dict = self.get_orf_dna_sequence(self.input_sequence, self.input_type)

        if self.input_type == "protein":
            submitted_proteins_dict = self.get_submitted_protein_sequence(self.input_sequence)

        with open(os.path.join(self.data, "VFDB.json")) as json_file:
            json_data = json.load(json_file)

        with open(self.xml_file, 'r') as result_handle:
            blast_records = NCBIXML.parse(result_handle)

            for blast_record in blast_records:
                perfect = {}
                strict = {}
                loose = {}

                for alignment in blast_record.alignments:
                    alignTitle = alignment.title
                    orfInfo = blast_record.query.encode('ascii', 'replace')

                    c = 0
                    barc = 0
                    for eachc in orfInfo:
                        if barc >= 6:
                            break
                        elif eachc == '|':
                            barc += 1
                            c += 1
                        else:
                            c += 1
                    orffrom = orfInfo[c:]

                    modelTypeID = self.extract_nth_bar(alignTitle, 0)

                    if modelTypeID == 40292:
                        spacepos = alignTitle.index(' ')
                        hitid = alignTitle[0:spacepos]
                        hitid = hitid.encode('ascii', 'replace')
                        modelDescrpt = alignTitle[alignTitle.index(' ') + 1:]
                        underscoreinMD = modelDescrpt.index('_')
                        modelID = modelDescrpt[0:underscoreinMD]
                        seqinModel = modelDescrpt[underscoreinMD + 1: modelDescrpt.index(' ')]

                        pass_bitscore = "{}".format(self.extract_nth_bar(alignment.title, 1))
                        pass_evalue = "{}".format("n/a")

                        # logger.info("pass_evalue: {}".format(pass_evalue))
                        # logger.info("pass_bitscore: {}".format(pass_bitscore))

                        init = 0

                        for hsp in alignment.hsps:
                            querySeq = hsp.query.replace('-', '')
                            realQueryLength = len(querySeq)
                            card_sequence = ""
                            orf_protein_sequence = ""
                            try:
                                card_sequence = str(
                                    json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"][
                                        "sequence"])
                            except Exception as e:
                                logger.warning(
                                    "Exception : {} -> {} -> Model({}) missing in database. Please generate new database.".format(
                                        type(e), e, modelID))

                            if predicted_genes_dict:
                                if orfInfo.strip() in predicted_genes_dict.keys():
                                    orf_protein_sequence = str(
                                        Seq(predicted_genes_dict[orfInfo.decode()], generic_dna).translate(
                                            table=11)).strip("*")
                                else:
                                    orf_protein_sequence = str(
                                        Seq(predicted_genes_dict[orfInfo.decode()[:orfInfo.decode().index(' # ')]],
                                            generic_dna).translate(table=11)).strip("*")

                            if submitted_proteins_dict:
                                orf_protein_sequence = str(submitted_proteins_dict[orfInfo.decode().split(" ")[0]])

                            if card_sequence == orf_protein_sequence:
                                """ Perfect hits """
                                # logger.info("Perfect hits")
                                ppinsidedict = {}
                                ppinsidedict["type_match"] = "Perfect"
                                ppinsidedict["model_id"] = modelID
                                ppinsidedict["orf_strand"] = self.extract_nth_bar(orfInfo.decode(), 0)
                                ppinsidedict["orf_start"] = self.extract_nth_bar(orfInfo.decode(), 1)
                                ppinsidedict["orf_end"] = self.extract_nth_bar(orfInfo.decode(), 2)
                                ppinsidedict["orf_from"] = orffrom.decode()
                                ppinsidedict["model_name"] = json_data[modelID]["model_name"]
                                ppinsidedict["model_type"] = json_data[modelID]["model_type"]
                                ppinsidedict["model_type_id"] = modelTypeID
                                ppinsidedict["pass_evalue"] = pass_evalue
                                ppinsidedict["pass_bitscore"] = pass_bitscore
                                ppinsidedict["ARO_accession"] = json_data[modelID]["ARO_accession"]
                                ppinsidedict["ARO_name"] = json_data[modelID]["ARO_name"]
                                ppinsidedict["ARO_category"] = json_data[modelID]["ARO_category"]
                                ppinsidedict["evalue"] = hsp.expect
                                ppinsidedict["bit_score"] = hsp.bits
                                ppinsidedict["max_identities"] = hsp.identities
                                ppinsidedict["cvterm_id"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["NCBI_taxonomy"][
                                    "NCBI_taxonomy_cvterm_id"]
                                ppinsidedict["query"] = hsp.query
                                ppinsidedict["match"] = hsp.match
                                ppinsidedict["sequence_from_db"] = hsp.sbjct
                                ppinsidedict["sequence_from_broadstreet"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"][
                                    "sequence"]
                                ppinsidedict["dna_sequence_from_broadstreet"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"][
                                    "sequence"]

                                if self.input_type == 'contig':
                                    ppinsidedict["query_start"] = self.extract_nth_hash(orfInfo.decode(), 1) + (
                                                hsp.query_start - 1) * 3
                                    ppinsidedict["query_end"] = self.extract_nth_hash(orfInfo.decode(), 1) + (
                                                hsp.query_start - 1) * 3 + realQueryLength * 3 - 1
                                    ppinsidedict["orf_strand"] = self.extract_nth_hash(orfInfo.decode(), 3)
                                    ppinsidedict["orf_start"] = self.extract_nth_hash(orfInfo.decode(), 1)
                                    ppinsidedict["orf_end"] = self.extract_nth_hash(orfInfo.decode(), 2)
                                    ppinsidedict["orf_from"] = self.extract_nth_hash(orfInfo.decode(), 0).rstrip()

                                    if orfInfo.decode().split(' # ')[0] in predicted_genes_dict:
                                        ppinsidedict["orf_dna_sequence"] = predicted_genes_dict[
                                            orfInfo.decode().split(' # ')[0]]
                                        ppinsidedict["orf_prot_sequence"] = str(
                                            Seq(predicted_genes_dict[orfInfo.decode().split(' # ')[0]],
                                                generic_dna).translate(table=11)).strip("*")
                                    else:
                                        ppinsidedict["orf_dna_sequence"] = ""
                                        ppinsidedict["orf_prot_sequence"] = ""

                                elif self.input_type == 'protein':
                                    ppinsidedict["query_start"] = hsp.query_start
                                    ppinsidedict["query_end"] = hsp.query_start + realQueryLength
                                    ppinsidedict["query_from"] = blast_record.query
                                    ppinsidedict["orf_prot_sequence"] = orf_protein_sequence

                                elif self.input_type == 'read':
                                    pass

                                ppinsidedict["perc_identity"] = float(
                                    format(float(ppinsidedict["max_identities"] * 100) / len(ppinsidedict["query"]),
                                           '.2f'))
                                perfect["{}|hsp_num:{}".format(hitid.decode(), init)] = ppinsidedict
                                init += 1

                            elif hsp.bits >= float(pass_bitscore):
                                """ Strict hits """
                                # logger.info("Strict hits")
                                insidedict = {}
                                insidedict["type_match"] = "Strict"
                                insidedict["orf_strand"] = self.extract_nth_bar(orfInfo.decode(), 0)
                                insidedict["orf_start"] = self.extract_nth_bar(orfInfo.decode(), 1)
                                insidedict["orf_end"] = self.extract_nth_bar(orfInfo.decode(), 2)
                                insidedict["orf_from"] = orffrom.decode()
                                insidedict["model_name"] = json_data[modelID]["model_name"]
                                insidedict["model_type"] = json_data[modelID]["model_type"]
                                insidedict["model_type_id"] = modelTypeID
                                insidedict["model_id"] = modelID
                                insidedict["pass_evalue"] = pass_evalue
                                insidedict["pass_bitscore"] = pass_bitscore
                                insidedict["ARO_accession"] = json_data[modelID]["ARO_accession"]
                                insidedict["ARO_name"] = json_data[modelID]["ARO_name"]
                                insidedict["ARO_category"] = json_data[modelID]["ARO_category"]
                                insidedict["evalue"] = hsp.expect
                                insidedict["bit_score"] = hsp.bits
                                insidedict["max_identities"] = hsp.identities
                                insidedict["cvterm_id"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["NCBI_taxonomy"][
                                    "NCBI_taxonomy_cvterm_id"]
                                insidedict["query"] = hsp.query
                                insidedict["match"] = hsp.match
                                insidedict["sequence_from_db"] = hsp.sbjct
                                insidedict["sequence_from_broadstreet"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"][
                                    "sequence"]
                                insidedict["dna_sequence_from_broadstreet"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"][
                                    "sequence"]

                                if self.input_type == 'contig':
                                    insidedict["query_start"] = self.extract_nth_hash(orfInfo.decode(), 1) + (
                                                hsp.query_start - 1) * 3
                                    insidedict["query_end"] = self.extract_nth_hash(orfInfo.decode(), 1) + (
                                                hsp.query_start - 1) * 3 + realQueryLength * 3 - 1
                                    insidedict["orf_strand"] = self.extract_nth_hash(orfInfo.decode(), 3)
                                    insidedict["orf_start"] = self.extract_nth_hash(orfInfo.decode(), 1)
                                    insidedict["orf_end"] = self.extract_nth_hash(orfInfo.decode(), 2)
                                    insidedict["orf_from"] = self.extract_nth_hash(orfInfo.decode(), 0).rstrip()

                                    if orfInfo.decode().split(' # ')[0] in predicted_genes_dict:
                                        insidedict["orf_dna_sequence"] = predicted_genes_dict[
                                            orfInfo.decode().split(' # ')[0]]
                                        insidedict["orf_prot_sequence"] = str(
                                            Seq(predicted_genes_dict[orfInfo.decode().split(' # ')[0]],
                                                generic_dna).translate(table=11)).strip("*")
                                    else:
                                        insidedict["orf_dna_sequence"] = ""
                                        insidedict["orf_prot_sequence"] = ""

                                elif self.input_type == 'protein':
                                    insidedict["query_start"] = hsp.query_start
                                    insidedict["query_end"] = hsp.query_start + realQueryLength
                                    insidedict["query_from"] = blast_record.query
                                    insidedict["orf_prot_sequence"] = orf_protein_sequence

                                elif self.input_type == 'read':
                                    pass

                                insidedict["perc_identity"] = float(
                                    format(float(insidedict["max_identities"] * 100) / len(insidedict["query"]), '.2f'))

                                strict["{}|hsp_num:{}".format(hitid.decode(), init)] = insidedict
                                init += 1

                            else:
                                """ Loose hits """
                                # logger.info("Loose hits")
                                linsidedict = {}
                                linsidedict["type_match"] = "Loose"
                                linsidedict["orf_strand"] = self.extract_nth_bar(orfInfo.decode(), 0)
                                linsidedict["orf_start"] = self.extract_nth_bar(orfInfo.decode(), 1)
                                linsidedict["orf_end"] = self.extract_nth_bar(orfInfo.decode(), 2)
                                linsidedict["orf_from"] = orffrom.decode().strip()
                                linsidedict["model_name"] = json_data[modelID]["model_name"]
                                linsidedict["model_type"] = json_data[modelID]["model_type"]
                                linsidedict["model_type_id"] = modelTypeID
                                linsidedict["pass_evalue"] = pass_evalue
                                linsidedict["pass_bitscore"] = pass_bitscore
                                linsidedict["model_id"] = modelID
                                linsidedict["ARO_accession"] = json_data[modelID]["ARO_accession"]
                                linsidedict["ARO_name"] = json_data[modelID]["ARO_name"]
                                linsidedict["ARO_category"] = json_data[modelID]["ARO_category"]
                                linsidedict["evalue"] = hsp.expect
                                linsidedict["max_identities"] = hsp.identities
                                linsidedict["bit_score"] = hsp.bits
                                linsidedict["cvterm_id"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["NCBI_taxonomy"][
                                    "NCBI_taxonomy_cvterm_id"]
                                linsidedict["query"] = hsp.query
                                linsidedict["match"] = hsp.match
                                linsidedict["sequence_from_db"] = hsp.sbjct
                                linsidedict["sequence_from_broadstreet"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["protein_sequence"][
                                    "sequence"]
                                linsidedict["dna_sequence_from_broadstreet"] = \
                                json_data[modelID]["model_sequences"]["sequence"][seqinModel]["dna_sequence"][
                                    "sequence"]

                                if self.input_type == 'contig':
                                    linsidedict["query_start"] = self.extract_nth_hash(orfInfo.decode(), 1) + (
                                                hsp.query_start - 1) * 3
                                    linsidedict["query_end"] = self.extract_nth_hash(orfInfo.decode(), 1) + (
                                                hsp.query_start - 1) * 3 + realQueryLength * 3 - 1
                                    linsidedict["orf_strand"] = self.extract_nth_hash(orfInfo.decode(), 3)
                                    linsidedict["orf_start"] = self.extract_nth_hash(orfInfo.decode(), 1)
                                    linsidedict["orf_end"] = self.extract_nth_hash(orfInfo.decode(), 2)
                                    linsidedict["orf_from"] = self.extract_nth_hash(orfInfo.decode(), 0)

                                    if orfInfo.decode().split(' # ')[0] in predicted_genes_dict:
                                        linsidedict["orf_dna_sequence"] = predicted_genes_dict[
                                            orfInfo.decode().split(' # ')[0]]
                                        linsidedict["orf_prot_sequence"] = str(
                                            Seq(predicted_genes_dict[orfInfo.decode().split(' # ')[0]],
                                                generic_dna).translate(table=11)).strip("*")
                                    else:
                                        linsidedict["orf_dna_sequence"] = ""
                                        linsidedict["orf_prot_sequence"] = ""

                                elif self.input_type == 'protein':
                                    linsidedict["query_start"] = hsp.query_start
                                    linsidedict["query_end"] = hsp.query_start + realQueryLength
                                    linsidedict["query_from"] = blast_record.query
                                    linsidedict["orf_prot_sequence"] = orf_protein_sequence

                                elif self.input_type == 'read':
                                    pass

                                linsidedict["perc_identity"] = float(
                                    format(float(linsidedict["max_identities"] * 100) / len(linsidedict["query"]),
                                           '.2f'))
                                loose["{}|hsp_num:{}".format(hitid.decode(), init)] = linsidedict

                                init += 1

                blastResults = self.results(blastResults, blast_record.query, perfect, strict, loose)

            return blastResults

