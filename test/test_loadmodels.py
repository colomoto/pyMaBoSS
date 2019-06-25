"""Test suite for loading models."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, set_nodes_istate
from os.path import dirname, join


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
		sim.update_parameters(**{"$fast": 1})
		sim.network.set_output(['Mdm2C', 'Mdm2N'])
		sim.mutate("Dam", "ON")
		res = sim.run()
		probas = res.get_last_states_probtraj().values[0]

		expected_probas = [0.437374, 0.041544, 0.210043, 0.31104]

		for i, proba in enumerate(probas):
			self.assertAlmostEqual(proba, expected_probas[i], delta=proba*1e-6)
			
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