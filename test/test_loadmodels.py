"""Test suite for loading models."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, loadBNet, loadSBML
from os.path import dirname, join, exists
import shutil

class TestLoadModels(TestCase):

	def test_load_p53_Mdm2(self):

		sim = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))
		self.assertEqual(sim.network['Mdm2C'].logExp, "$case_a ? p53_h : p53")

	def test_simulate_p53_Mdm2(self):

		sim = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))
		res = sim.run()

		res.plot_fixpoint()
		res.plot_trajectory(error=True)
		res.plot_node_trajectory(error=True)
		res.plot_entropy_trajectory()
		res.plot_piechart()

	def test_copy_p53_Mdm2(self):
		sim = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))
		sim_copy = sim.copy()

		self.assertEqual(str(sim.network), str(sim_copy.network))
		self.assertEqual(sim.str_cfg(), sim_copy.str_cfg())

	def test_check_p53_Mdm2(self):
		sim = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))
		errors = sim.check()
		self.assertEqual(len(errors), 0)

	def test_modifications_p53_Mdm2(self):
		sim = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))
		sim.update_parameters(sample_count=100)
		sim.network.set_output(['Mdm2C', 'Mdm2N'])
		sim.mutate("Dam", "ON")
		res = sim.run()
		probas = res.get_last_states_probtraj().values[0]

		expected_probas = [0.442395, 0.018827, 0.157108, 0.381669]

		for i, proba in enumerate(probas):
			self.assertAlmostEqual(proba, expected_probas[i], delta=proba*1e-6)

		if exists("saved_sim"):
			shutil.rmtree("saved_sim")
		res.save("saved_sim")
		self.assertTrue(exists("saved_sim"))
		self.assertTrue(exists("saved_sim/saved_sim.bnd"))
		self.assertTrue(exists("saved_sim/saved_sim.cfg"))
		self.assertTrue(exists("saved_sim/res_probtraj.csv"))
		self.assertTrue(exists("saved_sim/res_fp.csv"))
		self.assertTrue(exists("saved_sim/res_statdist.csv"))

	def test_load_multiple_cfgs(self):

		sim = load(join(dirname(__file__), "reprod_all.bnd"))

		sim2 = load(
			join(dirname(__file__), "p53_Mdm2.bnd"), 
			join(dirname(__file__), "p53_Mdm2_runcfg.cfg")
		)

		sim3 = load(
			join(dirname(__file__), "cellcycle.bnd"),
			join(dirname(__file__), "cellcycle_runcfg.cfg"),
			join(dirname(__file__), "cellcycle_runcfg-thread_1.cfg")
		)

	def test_type_istate(self):

		sim = load(
			join(dirname(__file__), "TregModel_InitPop.bnd"),
			join(dirname(__file__), "TregModel_InitPop_ActTCR2_TGFB.cfg")
		)

		istate = sim.network.get_istate()

		self.assertEqual([type(value) for value in istate["PTEN"].values()], [float, float])
		self.assertEqual([type(value) for value in istate[("TCR_b1", "TCR_b2", "CD28")].values()], [str, str, str])
		self.assertEqual([type(value) for value in istate[("PI3K_b1", "PI3K_b2")].values()], [float, float, float])
		self.assertEqual([type(value) for value in istate["TGFB"].values()], [str, str])

	def test_loadbnet(self):

		sim = loadBNet(
			join(dirname(__file__), "ensemble", "TC2_BN_0.bnet")
		)

		self.assertEqual(
			list(sim.network.keys()), 
			[
				'AHR', 'BCL6', 'CEBPB', 'CTCF', 'E2F3', 'E2F7', 'EBF1', 'EGR3', 'ESRRA', 'ETV5', 
				'FOSL1', 'FOSL2', 'FOXM1', 'FOXO3', 'HEY1', 'HIF1A', 'HMGA2', 'HSF1', 'HSF2', 
				'KLF15', 'KLF9', 'MAX', 'NFAT5', 'NFATC3', 'NFE2L2', 'NR1H3', 'NR2F1', 'NR2F2',
				'NR3C1', 'PPARG', 'RARA', 'RBPJ', 'RUNX2', 'SMAD3', 'SNAI1', 'SP3', 'STAT5A', 
				'TCF12', 'THAP11', 'TP53', 'TP63', 'VDR', 'XBP1', 'YBX1', 'YY1', 'ZNF143'
			]
		)
	
	def test_load_confusedparser(self):
		
		sim = load(
			join(dirname(__file__), "confused_parser.bnd"),
			join(dirname(__file__), "confused_parser.cfg") 
		)
		
		self.assertEqual(
			list(sim.network.keys()),
			['A', 'NOTH', 'B']
		)
		
	def test_load_reserved_names(self):

		with self.assertRaises(Exception) as context:
			sim = load(
				join(dirname(__file__), "reserved_names.bnd"),
				join(dirname(__file__), "reserved_names.cfg") 
			)
		# print(context.exception)
		self.assertTrue(
			   "Name NOT is reserved !" == str(context.exception)
		)

	def test_load_sbml(self):
		
		sim = loadSBML(
			join(dirname(__file__), "Cacace_TdevModel_2nov2020.sbml"),
			join(dirname(__file__), "Cacace_TdevModel_2nov2020.cfg"),
		)
		
			
		res = sim.run()
		
		self.assertEqual(
			list(res.get_last_states_probtraj().values), [1.0]
		)
		
		self.assertEqual(
			list(res.get_last_states_probtraj().columns), ['Id1 -- Flt3']
		)
		
	def test_load_sbml_cmaboss(self):
		
		ref_logical_rules = {
			'CEBPb': '((!CEBPb & CEBPa) & (Pu1_b1 & Pu1_b2)) | (CEBPb & (Pu1_b1 & Pu1_b2))', 
			'CEBPa': '(((Pu1_b1 & Pu1_b2) & !Foxo1) & Runx1_b1) & !Hes1', 
			'Pu1_b1': '(((((((((((Pu1_b1 & !Pax5) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & !TCF1) & (Runx1_b1 & !Runx1_b2)) & !MCSF) | ((((Pu1_b1 & !Pax5) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & !TCF1) & (Runx1_b1 & Runx1_b2))) | ((((Pu1_b1 & !Pax5) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & TCF1) & Runx1_b1)) | (((Pu1_b1 & !Pax5) & (Gata3_b1 & Gata3_b2)) & Runx1_b1)) | ((Pu1_b1 & Pax5) & Runx1_b1)) | (((((Pu1_b1 & !Pax5) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & !TCF1) & (Runx1_b1 & !Runx1_b2)) & MCSF)) & (!Pu1_b1 | (Pu1_b1 & !Pu1_b2))) | (Pu1_b1 & Pu1_b2)', 
			'Pu1_b2': '(((((Pu1_b1 & !Pax5) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & !TCF1) & (Runx1_b1 & !Runx1_b2)) & MCSF) & Pu1_b1', 
			'Foxo1': '((!CEBPa & !EBF1) & E2A_protein) | (!CEBPa & EBF1)', 
			'Runx1_b1': '(((((!Scl & Pu1_b1) | ((Scl & (Pu1_b1 & !Pu1_b2)) & !prog_ass_Eprot)) | (Scl & (Pu1_b1 & Pu1_b2))) | (((Scl & !Pu1_b1) & prog_ass_Eprot) | ((Scl & (Pu1_b1 & !Pu1_b2)) & prog_ass_Eprot))) & (!Runx1_b1 | (Runx1_b1 & !Runx1_b2))) | (Runx1_b1 & Runx1_b2)', 
			'Hes1': '((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & HEB_E2A) & NTC', 'EBF1': '(((((((((((!CEBPb & !CEBPa) & !Pu1_b1) & EBF1) & Pax5) & Foxo1) & E2A_protein) & Ets1) & !Gata3_b1) & !NTC) | (((((((((!CEBPb & !CEBPa) & Pu1_b1) & !EBF1) & Foxo1) & E2A_protein) & Ets1) & !Gata3_b1) & !NTC) & Stat5)) | ((((((((((!CEBPb & !CEBPa) & Pu1_b1) & EBF1) & !Pax5) & Foxo1) & E2A_protein) & Ets1) & !Gata3_b1) & !NTC) & Stat5)) | (((((((((!CEBPb & !CEBPa) & Pu1_b1) & EBF1) & Pax5) & Foxo1) & E2A_protein) & Ets1) & !Gata3_b1) & !NTC)', 
			'HEB_E2A': '((!Id2 & !Id3) & E2A_protein) & HEB', 
			'Bcl11b': '(((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & Gata3_b1) & TCF1) & HEB_E2A) & Runx1_b1) & NTC', 
			'Gfi1': '((!CEBPa & (!Pu1_b1 | (Pu1_b1 & !Pu1_b2))) & HEB_E2A) | (CEBPa & (!Pu1_b1 | (Pu1_b1 & !Pu1_b2)))', 
			'Id2': '(((Pu1_b1 & !EBF1) & !HEB_E2A) & !Bcl11b) & !Gfi1', 'Id1': '!Gfi1', 'Scl': '(((!Gata3_b1 & !HEB_E2A) & !Bcl11b) & Gfi1) | ((Gata3_b1 & !HEB_E2A) & !Bcl11b)', 'Lyl1': 'Pu1_b1 & !NTC', 'prog_ass_Eprot': '((((!Scl & !Lmo2) & Lyl1) & E2A_protein) | ((!Scl & Lmo2) & E2A_protein)) | (Scl & E2A_protein)', 'NTC': 'Notch1_rec & !Deltex', 'Stat5': 'IL7Ra_act', 'Id3': '(((((((((!Scl & !Pu1_b1) & !Lyl1) & prog_ass_Eprot) & !NTC) & Stat5) | ((((!Scl & !Pu1_b1) & Lyl1) & prog_ass_Eprot) & !NTC)) | (((((!Scl & (Pu1_b1 & Pu1_b2)) & !Lyl1) & prog_ass_Eprot) & !NTC) & Stat5)) | ((((!Scl & (Pu1_b1 & Pu1_b2)) & Lyl1) & prog_ass_Eprot) & !NTC)) | (((Scl & !Pu1_b1) & prog_ass_Eprot) & !NTC)) | (((Scl & (Pu1_b1 & Pu1_b2)) & prog_ass_Eprot) & !NTC)', 'Gata3_b1': '(((((((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !EBF1) & !TCF1) & HEB_E2A) & NTC) | ((((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !EBF1) & TCF1) & !HEB_E2A) & Bcl11b) & NTC)) | (((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !EBF1) & TCF1) & HEB_E2A) & NTC)) | ((((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !EBF1) & TCF1) & !HEB_E2A) & !Bcl11b) & NTC)) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) | (Gata3_b1 & Gata3_b2)', 'E2A_protein': '!Id2 & E2A_gene', 'Scl_E2A': '(Scl & E2A_protein) & !HEB_E2A', 'Lmo2': '((Pu1_b1 & Pu1_b2) & !HEB_E2A) & Gfi1', 'Gfi1b': '((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & Gata3_b1) & HEB_E2A) & !Bcl11b) & NTC', 'Kit': '(((((((!Scl & !Lmo2) & prog_ass_Eprot) & !Gata3_b1) & !Bcl11b) & Stat5) | ((((!Scl & !Lmo2) & prog_ass_Eprot) & Gata3_b1) & !Bcl11b)) | (((!Scl & Lmo2) & prog_ass_Eprot) & !Bcl11b)) | ((Scl & prog_ass_Eprot) & !Bcl11b)', 'Flt3': '!Bcl11b', 'Pax5': '!CEBPa & EBF1', 'Gata3_b2': '((((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !EBF1) & TCF1) & !HEB_E2A) & !Bcl11b) & NTC) & Gata3_b1', 'TCF1': '(((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !EBF1) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & NTC', 'Runx1_b2': '(((Scl & !Pu1_b1) & prog_ass_Eprot) | ((Scl & (Pu1_b1 & !Pu1_b2)) & prog_ass_Eprot)) & Runx1_b1', 'MCSF': 'MCSF', 'Hhex': '((!Scl & Lmo2) & (!Pu1_b1 | (Pu1_b1 & !Pu1_b2))) | (Scl & (!Pu1_b1 | (Pu1_b1 & !Pu1_b2)))', 'Ikaros': '(Pu1_b1 & !Pu1_b2) & Runx1_b1', 'Ets1': '((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !E2A_protein) & Gata3_b1) & Bcl11b) | ((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & E2A_protein)', 'Bcl11a': '(Pu1_b1 & Pu1_b2) & !Gata3_b1', 'E2A_gene': '(((((!Pu1_b1 & Ikaros) & EBF1) & Pax5) | ((((Pu1_b1 & !Pu1_b2) & Ikaros) & !EBF1) & NTC)) | (((((Pu1_b1 & !Pu1_b2) & Ikaros) & EBF1) & !Pax5) & NTC)) | ((((Pu1_b1 & !Pu1_b2) & Ikaros) & EBF1) & Pax5)', 'Myb': 'Pu1_b1 & !Pu1_b2', 'CD25': '(TCF1 & NTC) & Stat5', 'Runx3': '(Scl & !Pu1_b1) & prog_ass_Eprot', 'HEB_gene': '(Pu1_b1 & !Pu1_b2) & NTC', 'HEB': 'HEB_gene', 'Lef1_b1': '(((TCF1 & NTC) | (!TCF1 & NTC)) & (!Lef1_b1 | (Lef1_b1 & !Lef1_b2))) | (Lef1_b1 & Lef1_b2)', 'Lef1_b2': '(!TCF1 & NTC) & Lef1_b1', 'pTa': '((((!Scl & !prog_ass_Eprot) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & HEB_E2A) & Bcl11b) & NTC', 'TCRb': '(((Ets1 & Gata3_b1) & HEB_E2A) & Bcl11b) & Runx1_b1', 'Rag1': '(((((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & !HEB_E2A) & (!Runx1_b1 | (Runx1_b1 & !Runx1_b2))) & !Gfi1) & NTC) | (((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & !HEB_E2A) & (!Runx1_b1 | (Runx1_b1 & !Runx1_b2))) & Gfi1)) | ((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & (!Gata3_b1 | (Gata3_b1 & !Gata3_b2))) & HEB_E2A) & (!Runx1_b1 | (Runx1_b1 & !Runx1_b2)))', 'CD3e': '(((((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !HEB_E2A) & !Bcl11b) & NTC) | (((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !HEB_E2A) & Bcl11b)) | ((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & HEB_E2A)', 'CD3g': '((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & HEB_E2A) & NTC', 'Lat': '(((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & !HEB_E2A) & NTC) | ((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & HEB_E2A)', 'Zap70': '((!Pu1_b1 | (Pu1_b1 & !Pu1_b2)) & HEB_E2A) & Bcl11b', 'Nrarp': 'NTC', 'Notch_gene_b1': '(((((((!Lyl1 & !Pax5) & HEB_E2A) & NTC) & Nrarp) | (((Lyl1 & !Pax5) & HEB_E2A) & Nrarp)) | (((((!Lyl1 & !Pax5) & HEB_E2A) & NTC) & !Nrarp) | (((Lyl1 & !Pax5) & HEB_E2A) & !Nrarp))) & (!Notch_gene_b1 | (Notch_gene_b1 & !Notch_gene_b2))) | (Notch_gene_b1 & Notch_gene_b2)', 'Notch_gene_b2': '(((((!Lyl1 & !Pax5) & HEB_E2A) & NTC) & !Nrarp) | (((Lyl1 & !Pax5) & HEB_E2A) & !Nrarp)) & Notch_gene_b1', 'Notch1_rec': 'Notch_gene_b1 & Delta', 'Deltex': '!HEB_E2A & NTC', 'Delta': 'Delta', 'IL7Ra_gene': '(!Pu1_b1 & Notch_gene_b1) | Pu1_b1', 'IL7': 'IL7', 'IL7Ra_act': 'IL7Ra_gene & IL7', 'CD45': 'Scl_E2A & (Gata3_b1 & Gata3_b2)', 'CD44': 'Pu1_b1'
		}
		
		sim = loadSBML(
			join(dirname(__file__), "Cacace_TdevModel_2nov2020.sbml"),
			join(dirname(__file__), "Cacace_TdevModel_2nov2020.cfg"),
			cmaboss=True
		)
		
		rules = sim.get_logical_rules()
		for node, rule in rules.items():
			self.assertEqual(rule, ref_logical_rules[node])
		
		
		res = sim.run()
		
		self.assertEqual(
			list(res.get_last_states_probtraj().values), [1.0]
		)
		
		self.assertEqual(
			list(res.get_last_states_probtraj().columns), ['Id1 -- Flt3']
		)
		
	def test_load_sbml_corral(self):
		
		sim = loadSBML(
			join(dirname(__file__), "Corral_ThIL17diff_15jan2021.sbml"),
		)
		
		sim.update_parameters(sample_count=1000, max_time=10)
		res = sim.run()
		
		self.assertEqual(
			list(res.get_last_states_probtraj().values[0]), [0.00179 , 0.001214, 0.996996]
		)

		self.assertEqual(
			list(res.get_last_states_probtraj().columns.values), 
			['IL12RB1 -- IL12RB2 -- GP130 -- STAT5B_b1 -- IL1R1 -- STAT5B_b2 -- CXCR4 -- IL2RB -- CGC', 
			'IL12RB1 -- IL12RB2 -- GP130 -- STAT5B_b1 -- IL1RAP -- IL1R1 -- CXCR4 -- IL2RB -- CGC', 
			'IL12RB1 -- IL12RB2 -- GP130 -- STAT5B_b1 -- IL1RAP -- IL1R1 -- STAT5B_b2 -- CXCR4 -- IL2RB -- CGC'
			]
		)
		
	
		