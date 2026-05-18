import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt

@pd.api.extensions.register_dataframe_accessor("viz")
class Visualiser:
    def __init__(self, pandas_obj=None, list_queries=None, list_of_results=None):
        self._obj = pandas_obj
        self.list_of_results = list_of_results
        self.list_queries = list_queries

    def evolution_over_time(self, top: int = 10):
        # On utilise self._obj au lieu de self
        if "Time" in self._obj.columns:
            df_indexed = self._obj.set_index("Time")
        else:
            df_indexed = self._obj

        mean_probs = df_indexed.mean().sort_values(ascending=False)
        top_nodes = mean_probs.head(top).index
        df_top = df_indexed[top_nodes]

        df_top.plot(figsize=(12, 6))

        plt.title(f"Individual probabilities of activation for the top {top}")
        plt.xlabel("Time")
        plt.ylabel("Probability")
        if not df_top.empty:
            plt.ylim(0, df_top.values.max() * 1.05)
        plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
        plt.grid(True, alpha=0.3)
        plt.show()


    def display_results_and_queries(self, title: str = ""):
        import IPython.display as idp
        i=0
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)

        if self.list_of_results is None:
            print("No results to display")
            return

        if title:
            print(title)

        for r in self.list_of_results:
            print(f"Query {i+1} : {self.list_queries[i]}")
            if r is not None:
                if hasattr(r, 'empty') and r.empty:
                    print(f"❌ Result {i} is empty")
                else:
                    idp.display(r)
            else:
                print(f"❌ Result {i} is None")
            i=i+1