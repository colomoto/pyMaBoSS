"""Test suite for converting models."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, to_biolqm
from os.path import dirname, join


class TestConvertModels(TestCase):

	def test_convert_p53_Mdm2(self):

		model = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))

		with self.assertRaises(Exception) as context:
			to_biolqm(model)

	def test_convert_reprod_all(self):

		model = load(join(dirname(__file__), "reprod_all.bnd"), join(dirname(__file__), "reprod_all.cfg"))
		to_biolqm(model)