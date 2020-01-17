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
			1.0, 0.6876669999999963, 0.632190840108978, 0.6105730743314213, 0.5970494913080288, 
			0.5757515418540318, 0.5434841224423094, 0.5025478113716569, 0.4591799454414765,
		 	0.4179639535386058, 0.3816972212900199, 0.3511778565673089, 0.32597663122430576
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

	def test_uppmaboss_cmaboss(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT_cmaboss', cmaboss=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6876667574786982, 0.6319814602026599, 0.6102102946885618, 0.5967351627970129, 
			0.5757742556205552, 0.5435351816149544, 0.5021936050349172, 0.4587211444452725, 
			0.4171611288839445, 0.381068843191937, 0.35043461533908826, 0.32536783024600635
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

	def test_uppmaboss_cmaboss_only_final_state(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT_cmaboss_final', cmaboss=True, only_final_state=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6765800000000068, 0.6259041579999869, 0.6073523587568533, 0.5918770206556948, 
			0.5660119948529954, 0.5279929691586801, 0.4834462023507227, 0.4389256415762149, 
			0.39814067096090383, 0.3631401245767077, 0.33461546779119583, 0.311319538923568
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

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



class TestUpPMaBoSSOverwrite(TestCase):

	def test_uppmaboss_overwrite(self):

		# Now again, but with a modified max_time, and with overwrite
		# Results should be different if overwriting indeed works
		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		sim.param["max_time"] = 2
		expected_pop_ratios = [
			1.0, 0.6313999999999872, 0.5972816695999633, 0.5398984304747627, 0.4534148003891122, 
			0.3769890152946865, 0.3237917183574193, 0.28743962213741264, 0.2597215319350639, 
			0.23693875915370644, 0.21775311700874098, 0.20174782740235453, 0.18839353346310012
		]

		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT', overwrite=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])


class TestUpPMaBoSSRestore(TestCase):

	def test_uppmaboss_restore(self):
		# Now again, but with save results (from the overwrite run)
		expected_pop_ratios = [
			1.0, 0.6313999999999872, 0.5972816695999633, 0.5398984304747627, 0.4534148003891122, 
			0.3769890152946865, 0.3237917183574193, 0.28743962213741264, 0.2597215319350639, 
			0.23693875915370646, 0.21775311700874095, 0.20174782740235453, 0.1883935334631001
		]

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT')
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

		uppmaboss_sim.save('results')
		uppmaboss_sim.results[0].plot_piechart()

		expected_state_tnf = [
			2.e-05, 0.e+00, 0.e+00, 0.e+00, 0.e+00, 4.e-06, 0.e+00, 
			0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00
		]
		for i, val in enumerate(uppmaboss_sim.get_stepwise_probability_distribution().loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_state_tnf[i])
		
		expected_node_tnf = [
			0.73327, 0.545001, 0.507857, 0.538481, 0.550555, 0.554288, 0.569911, 0.590148,
 			0.60991, 0.634384, 0.656962, 0.677894, 0.69656 
		]
		for i, val in enumerate(uppmaboss_sim.get_nodes_stepwise_probability_distribution(nodes=["TNF"]).loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_node_tnf[i])

		expected_sum = [
			0.71622,  0.452406, 0.37555,  0.407976, 0.424626, 0.414956, 0.412622, 0.412701,
 			0.412521, 0.414184, 0.410111, 0.402366, 0.393019
		]

		for i, val in enumerate(uppmaboss_sim.get_stepwise_probability_distribution(include=["TNF"], exclude=["NFkB"]).sum(axis=1).values):
			self.assertAlmostEqual(val, expected_sum[i])

		following_sim = UpdatePopulation(
			sim, 
			join(dirname(__file__), "CellFate_1h.upp"), 
			previous_run=uppmaboss_sim
		)
		following_sim.run()


class TestUpPMaBoSSRemote(TestCase):

	def test_uppmaboss_remote(self):

		sim = load(
			"https://raw.githubusercontent.com/sysbio-curie/UpPMaBoSS-docker/master/CellFateModel_uppmaboss.bnd",
			"https://raw.githubusercontent.com/sysbio-curie/UpPMaBoSS-docker/master/CellFateModel_uppmaboss.cfg"
		)
		uppmaboss_model = UpdatePopulation(sim, 
			"https://github.com/sysbio-curie/UpPMaBoSS-docker/blob/master/CellFateModel_uppmaboss.upp"
		)
		uppmaboss_sim = uppmaboss_model.run('remote')
	
class TestUpPMaBoSSWrite(TestCase):
	def test_uppmaboss_write(self):

		sim = load(
			"https://raw.githubusercontent.com/sysbio-curie/UpPMaBoSS-docker/master/CellFateModel_uppmaboss.bnd",
			"https://raw.githubusercontent.com/sysbio-curie/UpPMaBoSS-docker/master/CellFateModel_uppmaboss.cfg"
		)
		uppmaboss_model = UpdatePopulation(sim)

		uppmaboss_model.setDivisionNode("Division")
		uppmaboss_model.setDeathNode("Death")
		uppmaboss_model.setExternalVariable("$TNF_induc", "$ProdTNF_NFkB*p[(NFkB,Death) = (1,0)]")
		uppmaboss_model.setStepNumber(12)
		uppmaboss_sim = uppmaboss_model.run('defined')

		expected_pop_ratios = [
			1.0, 0.9222239999999877, 0.8468248102079586, 0.818488358408744, 0.8001501267385603, 
			0.7726665701852689, 0.730234040150328, 0.6782618230446756, 0.6211955863009171, 
			0.5665924942649925, 0.5182428903593317, 0.47718250615612784, 0.44280389250008473
		]
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])


