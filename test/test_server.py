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
			1.0, 0.6909369999999935, 0.6342905300549739, 0.6126149197713755, 0.5988359849958501, 
			0.5778204349383446, 0.545789536947916, 0.5061526634060919, 0.46399217115496494, 
			0.42322767496592445, 0.3869151636814832, 0.35611516899175727, 0.3307038588779905
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

