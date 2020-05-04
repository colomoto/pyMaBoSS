"""Test suite for uppmaboss simulations."""

#For testing in environnement with no screen
import matplotlib
matplotlib.use('Agg')

from unittest import TestCase
from maboss import load, Ensemble
from os import listdir
from os.path import dirname, join, splitext
from json import loads

class TestEnsembleMaBoSS(TestCase):

	def test_ensemble(self):

		ensemble_model = Ensemble(join(dirname(__file__), "ensemble"), join(dirname(__file__), "simple_config.cfg"))
		results = ensemble_model.run()
		results.get_fptable()
		results.get_states_probtraj()

	def test_ensemble_zip(self):

		ensemble_model = Ensemble(join(dirname(__file__), "ensemble.zip"), join(dirname(__file__), "simple_config.cfg"))
		results = ensemble_model.run()
		results.get_fptable()
		results.get_states_probtraj()

	def test_ensemble_individual(self):

		ensemble_model = Ensemble(
			join(dirname(__file__), "ensemble"),
			join(dirname(__file__), "simple_config.cfg"),
			outputs=['AHR', 'BCL6', 'CEBPB'],
			individual_results=True
		)
		self.assertEqual(len(ensemble_model.get_mini_bns()), 5)
		results = ensemble_model.run()

		results.plotSteadyStatesDistribution()
		results.plotSteadyStatesNodesDistribution()

	def test_ensemble_individual_mutant(self):

		ensemble_model = Ensemble(
			join(dirname(__file__), "ensemble"),
			join(dirname(__file__), "simple_config.cfg"),
			outputs=['AHR', 'BCL6', 'CEBPB'],
			mutations={'AHR': 'ON', 'BCL6': 'OFF'},
			individual_results=True
		)
		self.assertEqual(len(ensemble_model.get_mini_bns()), 5)
		results = ensemble_model.run()

		results.plotSteadyStatesDistribution()
		results.plotSteadyStatesNodesDistribution()

		results.get_individual_states_probtraj()
		results.get_individual_nodes_probtraj()

	def test_ensemble_initial_conditions(self):
		
		root_path = join(dirname(__file__), "ensemble2")

		models_files = {
			filename: join(root_path, filename) 
			for filename in listdir(root_path) 
			if filename.endswith(".bnet")
		}
		
		istates_files = {
			splitext(filename)[0]+".bnet": join(root_path, filename) 
			for filename in listdir(root_path) 
			if filename.endswith(".json")
		}
		
		individual_istates = {}
		for name, filename in istates_files.items():
			with open(filename, 'r') as f:
				json_data = loads(f.read())
				istate = {node.replace("-", "_"): value for node, value in json_data['states']['AD15'].items()}
				individual_istates.update({name: istate})

		ensemble_model = Ensemble(
			root_path,
			outputs=['ADIPOQ', 'CEBPA', 'FABP4', 'LPL'],
			mutations={'JUN': 'ON',	'TTF1': 'ON', 'ESR1': 'OFF', 'NFKB1': 'OFF'},
			individual_istates=individual_istates,
			individual_results=True
		)
		self.assertEqual(len(ensemble_model.get_mini_bns()), 11)
		results = ensemble_model.run()

		results.plotSteadyStatesDistribution()
		results.plotSteadyStatesNodesDistribution()



	def test_ensemble_initial_conditions_subset(self):
		
		root_path = join(dirname(__file__), "ensemble2")

		models_files = {
			filename: join(root_path, filename) 
			for filename in listdir(root_path) 
			if filename.endswith(".bnet")
		}
		
		istates_files = {
			splitext(filename)[0]+".bnet": join(root_path, filename) 
			for filename in listdir(root_path) 
			if filename.endswith(".json")
		}
		
		individual_istates = {}
		for i, (name, filename) in enumerate(istates_files.items()):
			if i > 3:
				with open(filename, 'r') as f:
					json_data = loads(f.read())
					istate = {node.replace("-", "_"): value for node, value in json_data['states']['AD15'].items()}
					individual_istates.update({name: istate})

		ensemble_model = Ensemble(
			root_path,
			outputs=['ADIPOQ', 'CEBPA', 'FABP4', 'LPL'],
			mutations={'JUN': 'ON',	'TTF1': 'ON', 'ESR1': 'OFF', 'NFKB1': 'OFF'},
			models=individual_istates.keys(),
			individual_istates=individual_istates,
			individual_results=True
		)
		self.assertEqual(len(ensemble_model.get_mini_bns()), 7)
		results = ensemble_model.run()

		results.plotSteadyStatesDistribution()
		results.plotSteadyStatesNodesDistribution()

