import sys
import os
import unittest
import shutil
from io import StringIO
sys.path.append(".")
from mock_gff3 import Create_generator
from mock_helper import import_data
import annogesiclib.detect_utr as du
from mock_args_container import MockClass


class Mock_func(object):

    def __init__(self):
        self.example = Example()

    def mock_read_file(self, tss_file, gff_file, ta_file, term_file):
        if term_file is None:
            return self.example.genes, self.example.cdss, \
                   None, self.example.tsss, self.example.tas, True
        if tss_file is None:
            return self.example.genes, self.example.cdss, \
                   self.example.terms, None, self.example.tas, True

    def mock_plot(self, utr, utr_pri, utr_sec, filename, source,
                  utr_type, base_5utr):
        pass

class TestDetectUTR(unittest.TestCase):

    def setUp(self):
        self.example = Example()
        self.mock_args = MockClass()
        self.test_folder = "test_folder"
        if (not os.path.exists(self.test_folder)):
            os.mkdir(self.test_folder)

    def tearDown(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

    def test_import_utr(self):
        args = self.mock_args.mock()
        utr_all = {"pri": [], "all": [], "sec": []}
        utr_strain = {"pri": {"aaa": []}, "all": {"aaa": []},
                      "sec": {"aaa": []}}
        args.source = True
        args.base_5utr = "both"
        args.fuzzy_5utr = 5
        detect = du.import_utr(self.example.tss_fit, utr_strain, utr_all, 140,
                               340, self.example.tas, 200, args)
        self.assertTrue(detect[0])
        self.assertDictEqual(utr_strain, {'pri': {'aaa': [200]},
                             'all': {'aaa': [200]}, 'sec': {'aaa': []}})
        self.assertDictEqual(utr_all, {'pri': [200], 'all': [200], 'sec': []})
        detect = du.import_utr(
            self.example.tss_nofit, utr_strain, utr_all, 1140, 1190,
            self.example.tas, 50, args)
        self.assertFalse(detect[0])
        self.assertDictEqual(utr_strain, {'pri': {'aaa': [200]},
                                          'all': {'aaa': [200]},
                                          'sec': {'aaa': []}})
        self.assertDictEqual(utr_all, {'pri': [200], 'all': [200], 'sec': []})

    def test_detect_cds(self):
        nears = []
        names = []
        checks = []
        for gene in self.example.genes:
            near_cds, cds_name, check_utr = du.detect_cds(
                self.example.cdss, gene)
            nears.append(near_cds.start)
            names.append(cds_name)
            checks.append(check_utr)
        self.assertEqual(set(nears), set([148, 220, 5400]))
        self.assertEqual(set(names), set([
            'YP_000001', 'AAA_00002', 'CDS:5400-5800_r']))
        self.assertEqual(set(checks), set([True, True, True]))

    def test_check_associated_TSSpredator(self):
        check_utr, cds_name, near_cds = du.check_associated_TSSpredator(
            self.example.genes, self.example.tss_fit,
            self.example.cdss, False, "NA", "AAA_00001")
        self.assertTrue(check_utr)
        self.assertEqual(cds_name, "YP_000001")
        self.assertEqual(near_cds.start, 148)
        check_utr, cds_name, near_cds = du.check_associated_TSSpredator(
            self.example.genes, self.example.tss_nofit,
            self.example.cdss, False, "NA", "AAA_01001")
        self.assertFalse(check_utr)
        self.assertEqual(cds_name, "NA")
        self.assertEqual(near_cds, None)

    def test_get_5utr_from_TSSpredator(self):
        utr_datas = du.get_5utr_from_TSSpredator(
            self.example.tss_fit, self.example.genes,
            self.example.cdss)
        self.assertTrue(utr_datas["check"])
        self.assertEqual(utr_datas["cds_name"], 'YP_000001')
        self.assertEqual(utr_datas["locus"], 'AAA_00001')
        self.assertEqual(utr_datas["near_cds"].start, 148)
        utr_datas = du.get_5utr_from_TSSpredator(
            self.example.tss_nofit, self.example.genes,
            self.example.cdss)
        self.assertFalse(utr_datas["check"])
        self.assertEqual(utr_datas["cds_name"], None)
        self.assertEqual(utr_datas["locus"], None)
        self.assertEqual(utr_datas["near_cds"], None)

    def test_get_5utr_from_other(self):
        utr_datas = du.get_5utr_from_other(
            self.example.tss_fit, self.example.genes,
            self.example.cdss, 300)
        self.assertTrue(utr_datas["check"])
        self.assertEqual(utr_datas["cds_name"], 'YP_000001')
        self.assertEqual(utr_datas["locus"], 'AAA_00001')
        self.assertEqual(utr_datas["near_cds"].start, 148)
        utr_datas = du.get_5utr_from_other(
            self.example.tss_nofit, self.example.genes,
            self.example.cdss, 300)
        self.assertFalse(utr_datas["check"])
        self.assertEqual(utr_datas["cds_name"], None)
        self.assertEqual(utr_datas["locus"], None)
        self.assertEqual(utr_datas["near_cds"], None)

    def test_compare_ta(self):
        args = self.mock_args.mock()
        args.length = 300
        out = StringIO()
        utr_all = {"pri": [], "all": [], "sec": []}
        utr_strain = {"pri": {"aaa": []}, "all": {"aaa": []},
                      "sec": {"aaa": []}}
        du.compare_ta(self.example.tas, self.example.genes,
                      self.example.cdss, utr_strain, utr_all, out, args)
        self.assertEqual(set(out.getvalue().split("\n")[:-1]),
                         set([self.example.out_5utr]))
        out.close()

    def test_detect_5utr(self):
        args = self.mock_args.mock()
        du.read_file = Mock_func().mock_read_file
        du.plot = Mock_func().mock_plot
        out_file = os.path.join(self.test_folder, "5utr.gff")
        args.source = True
        args.base_5utr = "both"
        args.length = 300
        du.detect_5utr("test.tss", "test.gff", "test.ta", out_file, args)
        header = ["##gff-version 3"]
        args.source = False
        args.base_5utr = "both"
        du.detect_5utr("test.tss", "test.gff", "test.ta", out_file, args)
        datas = import_data(out_file)
        ref = header + [self.example.out_5utr_other]
        self.assertEqual(datas[1], ref[1])
        args.base_5utr = "transcript"
        du.detect_5utr("test.tss", "test.gff", "test.ta", out_file, args)
        self.assertEqual(set(datas), set(ref))
        args.source = True
        args.base_5utr = "both"
        du.detect_5utr("test.tss", "test.gff", "test.ta", out_file, args)
        datas = import_data(out_file)
        ref = header + [self.example.out_5utr_tsspredator]
        self.assertListEqual(datas, ref)

    def test_compare_term(self):
        ta_dict = {"seq_id": "aaa", "source": "Refseq", "feature": "TSS",
                   "start": 138, "end": 540, "phase": ".", "strand": "+",
                   "score": "."}
        attributes_ta = {"ID": "tran0", "Name": "Transcript_0"}
        ta = Create_generator(ta_dict, attributes_ta, "gff")
        term = du.compare_term(ta, self.example.terms, 5)
        self.assertEqual(term.start, 530)

    def test_get_3utr(self):
        ta_dict = {"seq_id": "aaa", "source": "Refseq", "feature": "TSS",
                   "start": 138, "end": 540, "phase": ".", "strand": "+",
                   "score": "."}
        attributes_ta = {"ID": "tran0", "Name": "Transcript_0"}
        ta = Create_generator(ta_dict, attributes_ta, "gff")
        cds_dict = {"seq_id": "aaa", "source": "Refseq", "feature": "CDS",
                    "start": 150, "end": 500, "phase": ".", "strand": "+",
                    "score": "."}
        attributes_cds = {"ID": "cds0", "Name": "CDS_0"}
        cds = Create_generator(cds_dict, attributes_cds, "gff")
        attributes = ["ID=3utr0"]
        out = StringIO()
        utr_all = []
        utr_strain = {"aaa": []}
        args = self.mock_args.mock()
        args.length = 300
        args.base_3utr = "transcript"
        args.fuzzy_3utr = 10
        du.get_3utr(ta, cds, utr_all, utr_strain, attributes, 0, out, args)
        self.assertEqual(set(out.getvalue().split("\n")[:-1]),
                         set(self.example.out_3utr.split("\n")))
        out.close()

    def test_get_near_cds(self):
        ta_dict = {"seq_id": "aaa", "source": "Refseq", "feature": "TSS",
                   "start": 138, "end": 540, "phase": ".", "strand": "+",
                   "score": "."}
        attributes_ta = {"ID": "tran0", "Name": "Transcript_0"}
        ta = Create_generator(ta_dict, attributes_ta, "gff")
        attributes = ["ID=3utr0"]
        near_cds = du.get_near_cds(self.example.cdss,
                                   self.example.genes, ta, attributes)
        self.assertEqual(near_cds.start, 148)

    def test_detect_3utr(self):
        args = self.mock_args.mock()
        args.fuzzy = 5
        args.base_3utr = "transcript"
        args.fuzzy_3utr = 10
        args.length = 300
        du.read_file = Mock_func().mock_read_file
        du.plot = Mock_func().mock_plot
        out_file = os.path.join(self.test_folder, "3utr.gff")
        du.detect_3utr("test.ta", "test.gff", "test.term", out_file, args)
        datas = import_data(out_file)
        self.assertEqual(set(datas),
                         set(self.example.out_3utr_gff.split("\n")))

class Example(object):
    tss_fit_dict = {"seq_id": "aaa", "source": "Refseq", "feature": "TSS",
                    "start": 140, "end": 140, "phase": ".", "strand": "+",
                    "score": "."}
    attributes_fit = {"ID": "tss0", "Name": "TSS_0", "type": "Primary",
                      "associated_gene": "AAA_00001"}
    tss_fit = Create_generator(tss_fit_dict, attributes_fit, "gff")
    tss_nofit_dict = {"seq_id": "aaa", "source": "Refseq", "feature": "TSS",
                      "start": 1140, "end": 1140, "phase": ".", "strand": "+",
                      "score": "."}
    attributes_nofit = {"ID": "tss0", "Name": "TSS_0", "type": "Primary",
                        "associated_gene": "AAA_01001"}
    tss_nofit = Create_generator(tss_nofit_dict, attributes_nofit, "gff")
    ta_dict = [{"seq_id": "aaa", "source": "Refseq", "feature": "Transcript",
                "start": 140, "end": 367, "phase": ".", "strand": "+",
                "score": "."},
               {"seq_id": "aaa", "source": "Refseq", "feature": "Transcript",
                "start": 230, "end": 240, "phase": ".", "strand": "+",
                "score": "."},
               {"seq_id": "bbb", "source": "Refseq", "feature": "Transcript",
                "start": 430, "end": 5167, "phase": ".", "strand": "-",
                "score": "."}]
    attributes_tas = [
        {"ID": "tran0", "Name": "Transcript_0", "locus_tag": "AAA_00001"},
        {"ID": "tran1", "Name": "Transcript_1", "locus_tag": "AAA_00002"},
        {"ID": "tran2", "Name": "Transcript_2", "locus_tag": "BBB_00001"}]
    term_dict = [{"seq_id": "aaa", "source": "Refseq",
                  "feature": "Terminator", "start": 360,
                  "end": 367, "phase": ".", "strand": "+", "score": "."},
                 {"seq_id": "aaa", "source": "Refseq",
                  "feature": "Terminator", "start": 530,
                  "end": 540, "phase": ".", "strand": "+", "score": "."},
                 {"seq_id": "bbb", "source": "Refseq",
                  "feature": "Terminator", "start": 420,
                  "end": 429, "phase": ".", "strand": "-", "score": "."}]
    attributes_term = [
        {"ID": "term0", "Name": "Terminator_0", "locus_tag": "AAA_00001"},
        {"ID": "term1", "Name": "Terminator_1", "locus_tag": "AAA_00002"},
        {"ID": "term2", "Name": "Terminator_2", "locus_tag": "BBB_00001"}]
    tss_dict = [{"seq_id": "aaa", "source": "Refseq", "feature": "TSS",
                 "start": 140, "end": 140, "phase": ".", "strand": "+",
                 "score": "."},
                {"seq_id": "aaa", "source": "Refseq", "feature": "TSS",
                 "start": 230, "end": 230, "phase": ".", "strand": "+",
                 "score": "."},
                {"seq_id": "bbb", "source": "Refseq", "feature": "TSS",
                 "start": 5166, "end": 5166, "phase": ".", "strand": "-",
                 "score": "."}]
    attributes_tss = [{"ID": "tss0", "Name": "TSS_0", "type": "Primary",
                       "associated_gene": "AAA_00001"},
                      {"ID": "tss1", "Name": "TSS_1", "type": "Internal",
                       "associated_gene": "AAA_00002"},
                      {"ID": "tss2", "Name": "TSS_2", "type": "Orphan",
                       "associated_gene": "orphan"}]
    gene_dict = [{"seq_id": "aaa", "source": "Refseq", "feature": "gene",
                  "start": 148, "end": 360, "phase": ".", "strand": "+",
                  "score": "."},
                 {"seq_id": "aaa", "source": "Refseq", "feature": "gene",
                  "start": 220, "end": 239, "phase": ".", "strand": "+",
                  "score": "."},
                 {"seq_id": "bbb", "source": "Refseq", "feature": "gene",
                  "start": 5400, "end": 5800, "phase": ".", "strand": "-",
                  "score": "."}]
    cds_dict = [{"seq_id": "aaa", "source": "Refseq", "feature": "CDS",
                 "start": 148, "end": 360, "phase": ".", "strand": "+",
                 "score": "."},
                {"seq_id": "aaa", "source": "Refseq", "feature": "rRNA",
                 "start": 220, "end": 239, "phase": ".", "strand": "+",
                 "score": "."},
                {"seq_id": "bbb", "source": "Refseq", "feature": "CDS",
                 "start": 5400, "end": 5800, "phase": ".", "strand": "-",
                 "score": "."}]
    attributes_gene = [
        {"ID": "gene0", "Name": "Gene_0", "locus_tag": "AAA_00001"},
        {"ID": "gene1", "Name": "Gene_1", "locus_tag": "AAA_00002"},
        {"ID": "gene2", "Name": "Gene_2", "locus_tag": "BBB_00001"}]
    attributes_cds = [{"ID": "cds0", "Name": "CDS_0",
                       "locus_tag": "AAA_00001", "protein_id": "YP_000001",
                       "Parent": "gene0"},
                      {"ID": "rna0", "Name": "rRNA_0",
                       "locus_tag": "AAA_00002"},
                      {"ID": "cds2", "Name": "CDS_1"}]
    out_5utr = """aaa\tANNOgesic\t5UTR\t140\t148\t.\t+\t.\tID=aaa_utr5_0;Name=5'UTR_00000;length=8;associated_cds=YP_000001;associated_gene=AAA_00001;Parent=tran0"""
    out_5utr_tsspredator = """aaa\tANNOgesic\t5UTR\t140\t148\t.\t+\t.\tID=aaa_utr5_0;Name=5'UTR_00000;length=8;associated_cds=YP_000001;associated_gene=AAA_00001;associated_tss=TSS_0;tss_type=Primary;Parent=tran0"""
    out_5utr_other = """aaa\tANNOgesic\t5UTR\t140\t148\t.\t+\t.\tID=aaa_utr5_0;Name=5'UTR_00000;length=8;associated_cds=YP_000001;associated_gene=AAA_00001;associated_tss=TSS_0;Parent=tran0"""
    out_3utr = """aaa\tANNOgesic\t3UTR\t500\t540\t.\t+\t.\tID=aaa_utr3_0;Name=3'UTR_00000;ID=3utr0;length=40;Parent=tran0"""
    out_3utr_gff = """##gff-version 3
aaa	ANNOgesic	3UTR	360	367	.	+	.	ID=aaa_utr3_0;Name=3'UTR_00000;associated_term=Terminator:360-367_+;length=7;Parent=tran0"""
    tas = []
    tsss = []
    terms = []
    genes = []
    cdss = []
    for index in range(0, 3):
        tas.append(Create_generator(ta_dict[index],
                                    attributes_tas[index], "gff"))
        terms.append(Create_generator(term_dict[index],
                                      attributes_term[index], "gff"))
        tsss.append(Create_generator(tss_dict[index],
                                     attributes_tss[index], "gff"))
        genes.append(Create_generator(gene_dict[index],
                                      attributes_gene[index], "gff"))
        cdss.append(Create_generator(cds_dict[index],
                                     attributes_cds[index], "gff"))
if __name__ == "__main__":
    unittest.main()

