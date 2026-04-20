import pandas as pd

class Extractor(object):

    @staticmethod
    def extract_column(df, column_name, exclusion: bool = False):
        out_df = df[["Time"]].copy()

        for col_name in df.columns:
            if col_name == "Time":
                continue

            if exclusion and column_name not in col_name:
                out_df[col_name] = df[col_name]
            elif not exclusion and column_name in col_name:
                out_df[col_name] = df[col_name]

        return out_df

    # todo wip (... [ A >= 0.5 & B | !C ]
    @staticmethod
    def extract_colum_numerical():
        pass