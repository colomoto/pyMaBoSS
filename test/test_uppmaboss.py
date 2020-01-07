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
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio*1e-2)

	def test_uppmaboss_cmaboss(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run(cmaboss=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6899230000000027, 0.6332961899289637, 0.6106773832094052, 0.596996988470672, 0.5764113383141323, 
			0.5451779135361446, 0.5052152821180231, 0.4627322342599125, 0.4215351834436775, 0.3854876022314294, 
			0.3557684355373424, 0.33079633751005605
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio*1e-2)

class TestUpPMaBoSSServer(TestCase):

	def test_uppmaboss_server(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run(host='localhost', port=7777)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6899230000000027, 0.6332961899289637, 0.6106773832094052, 0.596996988470672, 0.5764113383141323, 
			0.5451779135361446, 0.5052152821180231, 0.4627322342599125, 0.4215351834436775, 0.3854876022314294, 
			0.3557684355373424, 0.33079633751005605
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio/1e-6)



class TestUpPMaBoSSOverwrite(TestCase):

	def test_uppmaboss_overwrite(self):

		# Now again, but with a modified max_time, and with overwrite
		# Results should be different if overwriting indeed works
		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		sim.param["max_time"] = 2
		expected_pop_ratios = [
			1.0, 0.6284629999999846, 0.5871421862129369, 0.5177736854805769, 0.4238583410870101, 0.34499186727759734,
			0.29076190567646526, 0.2539398179415862, 0.2271176786113088, 0.20601231409098322, 0.18811025602109335,
			0.1740761022603733, 0.16198947625212115
		]

		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT', overwrite=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio / 1e-6)


class TestUpPMaBoSSRestore(TestCase):

	def test_uppmaboss_restore(self):
		# Now again, but with save results (from the overwrite run)
		expected_pop_ratios = [
			1.0, 0.6284629999999846, 0.5871421862129369, 0.5177736854805769, 0.4238583410870101, 0.34499186727759734,
			0.29076190567646526, 0.2539398179415862, 0.2271176786113088, 0.20601231409098322, 0.18811025602109335,
			0.1740761022603733, 0.16198947625212115
		]

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT')
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio / 1e-6)

		uppmaboss_sim.save('results')
		uppmaboss_sim.results[0].plot_piechart()

		expected_state_tnf = [3.3e-05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9e-06, 0.0, 0.0]
		for i, val in enumerate(uppmaboss_sim.get_stepwise_probability_distribution().loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_state_tnf[i], delta=val*0.1+0.001)
		
		expected_node_tnf = [
			0.7333250000000001, 0.5427929999999654, 0.5098009999999867, 0.538743999999904, 0.5516239999999077, 
			0.5621409999999166, 0.57624599999992, 0.5933839999999224, 0.6157929999999221, 0.6406789999999194, 
			0.662301999999913, 0.6821709999999142, 0.7047099999999183
		]
		for i, val in enumerate(uppmaboss_sim.get_nodes_stepwise_probability_distribution(nodes=["TNF"]).loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_node_tnf[i], delta=val*0.1+0.001)

		expected_sum = [
			0.716549, 0.449612, 0.37714000000000003, 0.406091, 0.42429, 0.421415, 0.4167240000000001, 0.412299, 
			0.41253199999999995, 0.41279499999999997, 0.406957, 0.39759399999999995, 0.384875
		]
		for i, val in enumerate(uppmaboss_sim.get_stepwise_probability_distribution(include=["TNF"], exclude=["NFkB"]).sum(axis=1).values):
			self.assertAlmostEqual(val, expected_sum[i], delta=val*0.1+0.001)

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
			1.0, 0.6284629999999846, 0.5871421862129369, 0.5177736854805769, 0.4238583410870101, 0.34499186727759734,
			0.29076190567646526, 0.2539398179415862, 0.2271176786113088, 0.20601231409098322, 0.18811025602109335,
			0.1740761022603733, 0.16198947625212115
		]
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i], delta=pop_ratio / 1e-6)


