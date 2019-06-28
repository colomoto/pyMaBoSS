"""Test suite for uppmaboss simulations."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, UpdatePopulation
from os.path import dirname, join


class TestUpPMaBoSS(TestCase):

	def test_uppmaboss(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT')
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6899230000000027, 0.6332961899289637, 0.6106773832094052, 0.596996988470672, 0.5764113383141323, 
			0.5451779135361446, 0.5052152821180231, 0.4627322342599125, 0.4215351834436775, 0.3854876022314294, 
			0.3557684355373424, 0.33079633751005605
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio/1e-6)
		
		# Now again, but with save results
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT')
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		
		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio/1e-6)

		# Now again, but with a modified max_time, and with overwrite
		# Results should be different if overwriting indeed works
		sim.param["max_time"] = 2
		expected_pop_ratios_2 = [
			1.0, 0.6284629999999846, 0.5871421862129369, 0.5177736854805769, 0.4238583410870101, 0.34499186727759734,
			0.29076190567646526, 0.2539398179415862, 0.2271176786113088, 0.20601231409098322, 0.18811025602109335,
			0.1740761022603733, 0.16198947625212115
		]

		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT', overwrite=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios_2[i], delta=pop_ratio / 1e-6)

		uppmaboss_sim.save('results')

		uppmaboss_sim.results[0].plot_piechart()
