"""Test suite for converting models."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, to_biolqm, to_minibn
from os.path import dirname, join


class TestConvertModels(TestCase):

	def test_convert_p53_Mdm2(self):

		model = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))
		with self.assertRaises(Exception) as context:
			to_biolqm(model)

	def test_convert_reprod_all(self):

		model = load(join(dirname(__file__), "reprod_all.bnd"), join(dirname(__file__), "reprod_all.cfg"))
		to_biolqm(model)

	def test_convert_reprod_all_minibn(self):

		model = load(join(dirname(__file__), "reprod_all.bnd"), join(dirname(__file__), "reprod_all.cfg"))
		minibn_model = to_minibn(model)
		self.assertEqual(
			sorted(list(minibn_model.keys())), 
			sorted([
				'ECMicroenv', 'DNAdamage', 'Migration', 'Metastasis', 'VIM', 'AKT2', 'ERK', 'miR200', 'AKT1', 
				'EMT', 'Invasion', 'p63', 'SMAD', 'CDH2', 'CTNNB1', 'CDH1', 'p53', 'p73', 'miR34', 'ZEB2', 
				'Apoptosis', 'miR203', 'p21', 'CellCycleArrest', 'GF', 'NICD', 'TGFbeta', 'TWIST1', 'SNAI2', 
				'ZEB1', 'SNAI1', 'DKK1'
			])
		)

	def test_initial_state(self):
		model = load(join(dirname(__file__), "reprod_all.bnd"), join(dirname(__file__), "reprod_all.cfg"))
		i1 = model.get_initial_state()
		model = load(join(dirname(__file__), "reprod_all.bnd"), join(dirname(__file__), "reprod_joined_init.cfg"))
		i2 = model.get_initial_state()
		self.assertEqual(set(i1.keys()), set(i2.keys()))
		self.assertEqual(i2["p63"], 1)
		self.assertEqual(i2["p53"], 1)
		self.assertEqual(i2["GF"], [0,1])
