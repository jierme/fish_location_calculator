import pandas as pd
from pathlib import Path
import math


def GetCross(x1, y1, x2, y2, x, y):
    a = (x2 - x1, y2 - y1)
    b = (x - x1, y - y1)
    return a[0] * b[1] - a[1] * b[0]


def isInSide(x1, y1, x2, y2, x3, y3, x4, y4, x, y):
    return GetCross(x1, y1, x2, y2, x, y) * GetCross(x3, y3, x4, y4, x, y) >= 0 \
           and GetCross(x2, y2, x3, y3, x, y) * GetCross(x4, y4, x1, y1, x, y) >= 0


def lo_check(data_before, fillna: bool = True):
    data_before = data_before[data_before.columns.drop(list(data_before.filter(regex='Flag')))]
    XY = data_before[['X1', 'Y1']].copy()
    columns_num = data_before.shape[1]
    for index in range(2, int(columns_num / 2 + 1)):
        X_index: str = 'X' + str(index)
        Y_index: str = 'Y' + str(index)
        XY.X1.fillna(data_before[X_index], inplace=True)
        XY.Y1.fillna(data_before[Y_index], inplace=True)
    if fillna == True:
        XY_full = XY.interpolate(method='linear',
                                 axis=0,
                                 limit=None,
                                 inplace=False,
                                 limit_direction=None,
                                 limit_area=None)

        XY_full.fillna(method="bfill", inplace=True)  # 这一行旨在解决部分鱼坐标在最开头有缺失值的问题
    else:
        XY_full = XY
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
        fish_index_xy = lo_check(fish_index_xy, fillna=True)
    else:
        fish_index_xy = lo_check(fish_index_xy, fillna=False)

    return fish_index_xy


def dis_points(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def fish_xy_cal(fish_index_xy: pd.merge,
                fps: float or int,
                video_tank_xy: float or int,
                real_tank_xy: float or int,
                bin_length: int):
    total_frame = fish_index_xy.shape[0]
    dis_frame_pix_list = []
    for frame in range(0, total_frame - 1):
        dis_frame_pix = math.sqrt(sum((fish_index_xy.iloc[frame] - fish_index_xy.iloc[frame + 1]) ** 2))
        dis_frame_pix_list.append(dis_frame_pix)
    dis_frame_pix_list.insert(0, None)

    new_xlsx_cal = pd.DataFrame()
    new_xlsx_cal['frame'] = range(0, total_frame)
    new_xlsx_cal['time(s)'] = new_xlsx_cal.frame / fps
    new_xlsx_cal['time(minute)'] = (new_xlsx_cal.frame / fps / 60).apply(lambda x: math.ceil(x))
    new_xlsx_cal['bin'] = (new_xlsx_cal['time(minute)'] / bin_length).apply(lambda x: math.ceil(x))

    new_xlsx_cal['x'] = fish_index_xy.X1
    new_xlsx_cal['y'] = fish_index_xy.Y1
    new_xlsx_cal['dis_frame_pix'] = dis_frame_pix_list
    new_xlsx_cal['dis_frame_real_mm'] = new_xlsx_cal.dis_frame_pix / video_tank_xy * real_tank_xy
    new_xlsx_cal['speed_frame_mm/s'] = new_xlsx_cal.dis_frame_real_mm * fps

    return new_xlsx_cal
