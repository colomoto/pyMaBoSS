"""Test suite for uppmaboss simulations."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, Ensemble
from os.path import dirname, join


class TestEnsembleMaBoSS(TestCase):

	def test_ensemble(self):

		ensemble_model = Ensemble(join(dirname(__file__), "ensemble"), join(dirname(__file__), "simple_config.cfg"))
		results = ensemble_model.run()
		results.get_fptable()
		results.get_states_probtraj()