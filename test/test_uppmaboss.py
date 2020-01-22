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
			1.0, 0.6909369999999935, 0.6342905300549739, 0.6126149197713755, 0.5988359849958501, 
			0.5778204349383446, 0.545789536947916, 0.5061526634060919, 0.46399217115496494, 
			0.42322767496592445, 0.3869151636814832, 0.35611516899175727, 0.3307038588779905
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

	def test_uppmaboss_cmaboss(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT_cmaboss', cmaboss=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6909624069153775, 0.6342955229629412, 0.612634017774106, 0.5987297245227169, 
			0.5776333504714077, 0.5459607679103569, 0.506353256457215, 0.4642648750518545, 
			0.42382723065620753, 0.38747995383853007, 0.3568792100813789, 0.33113257297246607
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

	def test_uppmaboss_cmaboss_only_final_state(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT_cmaboss_final', cmaboss=True, only_final_state=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6786400000000071, 0.6284342127999876, 0.6096251768108647, 0.5944394136564721, 
			0.5687655753806159, 0.5317559993905541, 0.48768406216106275, 0.44404609227886305, 
			0.40342031529624084, 0.3687463391964934, 0.3397997515695626, 0.3161428928652855
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
			1.0, 0.6332519999999854, 0.5980894161959628, 0.5412069260897618, 0.4565058773289611, 
			0.38047893201267624, 0.3277494982618138, 0.2906564487960144, 0.26264588682552875, 
			0.23994802928605113, 0.2206204554750762, 0.20436425783383877, 0.19093691300137253
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
			1.0, 0.6332519999999854, 0.5980894161959628, 0.5412069260897618, 0.4565058773289611, 
			0.38047893201267613, 0.3277494982618138, 0.2906564487960144, 0.26264588682552875, 
			0.23994802928605116, 0.2206204554750762, 0.2043642578338388, 0.19093691300137253
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
			3.e-06, 0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00,
			0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00,
 			]
		for i, val in enumerate(uppmaboss_sim.get_stepwise_probability_distribution().loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_state_tnf[i])
		
		expected_node_tnf = [
			0.733802, 0.543083, 0.509887, 0.542557, 0.554522, 0.562108, 0.577199, 0.598796,
			0.622496, 0.644773, 0.667594, 0.690237, 0.709729,
		]
		for i, val in enumerate(uppmaboss_sim.get_nodes_stepwise_probability_distribution(nodes=["TNF"]).loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_node_tnf[i])

		expected_sum = [
			0.717116, 0.446728, 0.372869, 0.407334, 0.425018, 0.419163, 0.412908, 0.413412,
			0.41431,  0.411403, 0.404932, 0.396315, 0.384204
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


