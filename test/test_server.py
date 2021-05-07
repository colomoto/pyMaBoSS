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
			+ "#1\t0.90536\tMdm2N\t1\t0\t0\t0\t0\n"
		)

		res.get_states_probtraj()
		res.get_statdist_clusters()
		res.get_fptable()
		mbcli.close()


class TestUpPMaBoSSServer(TestCase):

	def test_uppmaboss_server(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run(host='localhost', port=7777)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6907579999999945, 0.6341980442019741, 0.6126727283836865, 0.5992233366501704, 
			0.5788557354373725, 0.5473173595477481, 0.5081754112622799, 0.4654525962620004, 
			0.4247217704682538, 0.3886947462882363, 0.3581526679038661, 0.3328878624045683
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])
