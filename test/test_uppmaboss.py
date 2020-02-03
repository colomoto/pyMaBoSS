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
			1.0, 0.6907579999999945, 0.6341980442019741, 0.6126727283836865, 0.5992233366501704, 
			0.5788557354373725, 0.5473173595477481, 0.5081754112622799, 0.4654525962620004, 
			0.4247217704682538, 0.3886947462882363, 0.3581526679038661, 0.3328878624045683
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

	def test_uppmaboss_cmaboss(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT_cmaboss', cmaboss=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6907820416914479, 0.6341903631891185, 0.612996053462505, 0.5996083687781087, 
			0.5788914827739509, 0.5466795703259922, 0.5075723301828101, 0.46462393081796144, 
			0.4237712222056809, 0.388072085864841, 0.35730025864566073, 0.3320260202532354
		]

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])

	def test_uppmaboss_cmaboss_only_final_state(self):

		sim = load(join(dirname(__file__), "CellFateModel.bnd"), join(dirname(__file__), "CellFateModel_1h.cfg"))
		uppmaboss_model = UpdatePopulation(sim, join(dirname(__file__), "CellFate_1h.upp"))
		uppmaboss_sim = uppmaboss_model.run('WT_cmaboss_final', cmaboss=True, only_final_state=True)
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()
		expected_pop_ratios = [
			1.0, 0.6778600000000088, 0.6279830611999899, 0.6097213137802712, 0.594362433886137, 
			0.5680084035675778, 0.5307981730498335, 0.4871453312981917, 0.4427225485370628, 
			0.4022798437281834, 0.367703891159712, 0.3393539211512898, 0.31562968852360135
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
			1.0, 0.6323979999999877, 0.5972195964539613, 0.5413299949589563, 0.4570216375540166, 
			0.3810664694790497, 0.3280296382569338, 0.29096852169701004, 0.26290169809410047, 
			0.23962359303974, 0.2201920366329486, 0.2039266710788974, 0.19007637943255015
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
			1.0, 0.6323979999999877, 0.5972195964539613, 0.5413299949589563, 0.4570216375540166, 
			0.3810664694790497, 0.3280296382569338, 0.29096852169701004, 0.26290169809410047, 
			0.23962359303974, 0.2201920366329486, 0.2039266710788974, 0.19007637943255015
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
			1.7e-05, 0.e+00, 0.e+00, 0.e+00, 5.0e-06, 0.e+00, 0.e+00,
			0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00, 0.e+00,
 			]
		for i, val in enumerate(uppmaboss_sim.get_stepwise_probability_distribution().loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_state_tnf[i])
		
		expected_node_tnf = [
			0.736098, 0.542901, 0.507657, 0.541154, 0.555409, 0.562324, 0.576159, 0.598795,
 			0.622031, 0.644684, 0.666123, 0.688512, 0.70853 
		]
		for i, val in enumerate(uppmaboss_sim.get_nodes_stepwise_probability_distribution(nodes=["TNF"]).loc[:, "TNF"].values):
			self.assertAlmostEqual(val, expected_node_tnf[i])

		expected_sum = [
			0.719123, 0.446561, 0.37057,  0.405835, 0.425728, 0.41935,  0.412577, 0.413467,
 			0.414721, 0.412329, 0.405407, 0.396948, 0.384865,
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
			1.0, 0.9218339999999924, 0.8467423241939606, 0.8180987248510877, 0.7990468417467085, 
			0.7717098511967935, 0.7300537251389624, 0.677575273214723, 0.6208988119113313, 
			0.5665235984581267, 0.5183656934475426, 0.4771136331972621, 0.4430243412189205
		]
		pop_ratios = uppmaboss_sim.get_population_ratios('WT').values.tolist()

		for i, pop_ratio in enumerate(pop_ratios):
			self.assertAlmostEqual(pop_ratio, expected_pop_ratios[i])


