"""Test suite for simulation probability distributions."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')
import pandas, numpy

from unittest import TestCase
from maboss import load, set_nodes_istate
from os.path import dirname, join


class TestProbTrajs(TestCase):

	def test_probtraj_p53_Mdm2(self):

		path = dirname(__file__)
		sim = load(join(path, "p53_Mdm2.bnd"), join(path, "p53_Mdm2_runcfg.cfg"))
		res = sim.run()

		res_states_probtraj = pandas.read_csv(
			join(path, "res", "p53_Mdm2_states_probtraj.csv"), index_col=0, header=0
		)
		
		res_last_states_probtraj = pandas.read_csv(
			join(path, "res", "p53_Mdm2_last_states_probtraj.csv"), index_col=0, header=0
		)
		
		res_nodes_probtraj = pandas.read_csv(
			join(path, "res", "p53_Mdm2_nodes_probtraj.csv"), index_col=0, header=0
		)

		self.assertTrue(numpy.isclose(
			res.get_states_probtraj().sort_index(axis=1), 
			res_states_probtraj.sort_index(axis=1)
		).all())

		self.assertTrue(numpy.isclose(
			res.get_last_states_probtraj().sort_index(axis=1), 
			res_last_states_probtraj.sort_index(axis=1)
		).all())

		self.assertTrue(numpy.isclose(
			res.get_nodes_probtraj().sort_index(axis=1), 
			res_nodes_probtraj.sort_index(axis=1)
		).all())

	def test_probtraj_cellcycle(self):

		path = dirname(__file__)
		sim = load(
			join(path, "cellcycle.bnd"), 
			join(path, "cellcycle_runcfg.cfg"), 
			join(path, "cellcycle_runcfg-thread_1.cfg")
		)
		res = sim.run()

		res_states_probtraj = pandas.read_csv(
			join(path, "res", "cellcycle_states_probtraj.csv"), index_col=0, header=0
		)
		
		res_last_states_probtraj = pandas.read_csv(
			join(path, "res", "cellcycle_last_states_probtraj.csv"), index_col=0, header=0
		)
		
		res_nodes_probtraj = pandas.read_csv(
			join(path, "res", "cellcycle_nodes_probtraj.csv"), index_col=0, header=0
		)

		self.assertTrue(numpy.isclose(
			res.get_states_probtraj().sort_index(axis=1), 
			res_states_probtraj.sort_index(axis=1)
		).all())

		self.assertTrue(numpy.isclose(
			res.get_last_states_probtraj().sort_index(axis=1), 
			res_last_states_probtraj.sort_index(axis=1)
		).all())

		self.assertTrue(numpy.isclose(
			res.get_nodes_probtraj().sort_index(axis=1), 
			res_nodes_probtraj.sort_index(axis=1)
		).all())
