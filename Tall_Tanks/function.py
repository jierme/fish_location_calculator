import pandas as pd
from pathlib import Path


def lo_check(data_before):

    data_before = data_before[data_before.columns.drop(list(data_before.filter(regex='Flag')))]

    XY = data_before[['X1', 'Y1']].copy()
    columns_num = data_before.shape[1]
    for index in range(2, int(columns_num / 2 + 1)):
        X_index: str = 'X' + str(index)
        Y_index: str = 'Y' + str(index)

        XY.X1.fillna(data_before[X_index], inplace=True)
        XY.Y1.fillna(data_before[Y_index], inplace=True)

    XY_full = XY.interpolate(method='linear',
                             axis=0,
                             limit=None,
                             inplace=False,
                             limit_direction=None,
                             limit_area=None)

    XY_full.fillna(method="bfill", inplace=True)

    return XY_full


def lo_csvs_to_fishxy(path: Path, pattern: str, check: bool = True):

    lo_fish_index_i_csvs = path.glob(pattern)

    fish_index_xy = pd.DataFrame()
    file_count = 0
    for file in lo_fish_index_i_csvs:
        file_count = file_count + 1
        lo_index_file_data = pd.read_csv(file, na_values=0)
        fish_index_xy = pd.merge(fish_index_xy, lo_index_file_data,
                                 how='outer',
                                 left_index=True, right_index=True)

    if check:
        fish_index_xy = lo_check(fish_index_xy)
    return fish_index_xy

