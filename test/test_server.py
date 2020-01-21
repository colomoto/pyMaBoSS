"""Test suite for loading models."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, MaBoSSClient, UpdatePopulation
from os.path import dirname, join


class TestServer(TestCase):

	def test_run_p53_Mdm2(self):

		sim = load(join(dirname(__file__), "p53_Mdm2.bnd"), join(dirname(__file__), "p53_Mdm2_runcfg.cfg"))
		mbcli = MaBoSSClient(host="localhost", port=7777)
		res = mbcli.run(sim)

		self.assertEqual(
			res.getFP(),
			"Fixed Points (1)\n"
			+ "FP\tProba\tState\tMdm2N\tp53_h\tp53\tMdm2C\tDam\n"
			+ "#1\t0.90688\tMdm2N\t1\t0\t0\t0\t0\n"
		)

		res.get_states_probtraj()
		res.get_statdist_clusters()
		
		mbcli.close()


class TestUpPMaBoSSServer(TestCase):

	def test_uppmaboss_server(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run(host='localhost', port=7777)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6876669999999963, 0.632190840108978, 0.6105730743314213, 0.5970494913080288, 
			0.5757515418540318, 0.5434841224423094, 0.5025478113716569, 0.4591799454414765,
		 	0.4179639535386058, 0.3816972212900199, 0.3511778565673089, 0.32597663122430576
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

