import pandas as pd
from pathlib import Path
import math
import re
from scipy.stats import gaussian_kde
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf


def GetCross(x1, y1, x2, y2, x, y):
    a = (x2 - x1, y2 - y1)
    b = (x - x1, y - y1)
    return a[0] * b[1] - a[1] * b[0]


def isInSide(x1, y1, x2, y2, x3, y3, x4, y4, x, y):
    return GetCross(x1, y1, x2, y2, x, y) * GetCross(x3, y3, x4, y4, x, y) >= 0 \
           and GetCross(x2, y2, x3, y3, x, y) * GetCross(x4, y4, x1, y1, x, y) >= 0


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


def maze_heatmap(x, y, pic_path):
    xy = np.vstack([x, y])
    z = gaussian_kde(xy)(xy)
    fig, ax = plt.subplots()
    scatter_fig = ax.scatter(x, y, c=z, s=1)
    pic = plt.imread(pic_path)
    plt.imshow(pic)
    plt.colorbar(scatter_fig)
    return plt


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


def lo_Results(csv_results: pd.DataFrame, fish_index: int):
    mark_1_x = csv_results.X[(fish_index - 1) * 9 + 1]
    mark_2_x = csv_results.X[(fish_index - 1) * 9 + 2]
    mark_3_x = csv_results.X[(fish_index - 1) * 9 + 3]
    mark_4_x = csv_results.X[(fish_index - 1) * 9 + 4]
    mark_5_x = csv_results.X[(fish_index - 1) * 9 + 5]
    mark_6_x = csv_results.X[(fish_index - 1) * 9 + 6]
    mark_7_x = csv_results.X[(fish_index - 1) * 9 + 7]
    mark_8_x = csv_results.X[(fish_index - 1) * 9 + 8]
    mark_9_x = csv_results.X[(fish_index - 1) * 9 + 9]

    mark_1_y = csv_results.Y[(fish_index - 1) * 9 + 1]
    mark_2_y = csv_results.Y[(fish_index - 1) * 9 + 2]
    mark_3_y = csv_results.Y[(fish_index - 1) * 9 + 3]
    mark_4_y = csv_results.Y[(fish_index - 1) * 9 + 4]
    mark_5_y = csv_results.Y[(fish_index - 1) * 9 + 5]
    mark_6_y = csv_results.Y[(fish_index - 1) * 9 + 6]
    mark_7_y = csv_results.Y[(fish_index - 1) * 9 + 7]
    mark_8_y = csv_results.Y[(fish_index - 1) * 9 + 8]
    mark_9_y = csv_results.Y[(fish_index - 1) * 9 + 9]

    results = pd.DataFrame(
        {'x': [mark_1_x, mark_2_x, mark_3_x, mark_4_x, mark_5_x, mark_6_x, mark_7_x, mark_8_x, mark_9_x],
         'y': [mark_1_y, mark_2_y, mark_3_y, mark_4_y, mark_5_y, mark_6_y, mark_7_y, mark_8_y, mark_9_y]})

    return results


def dis_points(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def fish_xy_cal(fish_index_xy: pd.merge, fps: float or int, video_tank_xy: float or int, real_tank_xy: float or int):
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
    new_xlsx_cal['bin'] = (new_xlsx_cal['time(minute)'] / 10).apply(lambda x: math.ceil(x))
    new_xlsx_cal['x'] = fish_index_xy.X1
    new_xlsx_cal['y'] = fish_index_xy.Y1
    new_xlsx_cal['dis_frame_pix'] = dis_frame_pix_list
    new_xlsx_cal['dis_frame_real_mm'] = new_xlsx_cal.dis_frame_pix / video_tank_xy * real_tank_xy
    new_xlsx_cal['speed_frame_mm/s'] = new_xlsx_cal.dis_frame_real_mm * fps

    return new_xlsx_cal


def maze_arm(fish_index_xy: pd.DataFrame, lo_ref: pd.DataFrame):
    maze_arm_df = pd.DataFrame()

    maze_arm_df['arm_0'] = fish_index_xy[['X1', 'Y1']].apply(
        lambda x: isInSide(lo_ref.x[0], lo_ref.y[0], lo_ref.x[1], lo_ref.y[1],
                           lo_ref.x[2], lo_ref.y[2], lo_ref.x[3], lo_ref.y[3],
                           x[0], x[1]),
        axis=1)
    maze_arm_df['arm_5'] = fish_index_xy[['X1', 'Y1']].apply(
        lambda x: isInSide(lo_ref.x[3], lo_ref.y[3], lo_ref.x[4], lo_ref.y[4],
                           lo_ref.x[5], lo_ref.y[5], lo_ref.x[6], lo_ref.y[6],
                           x[0], x[1]),
        axis=1)
    maze_arm_df['arm_-3'] = fish_index_xy[['X1', 'Y1']].apply(
        lambda x: isInSide(lo_ref.x[6], lo_ref.y[6], lo_ref.x[7], lo_ref.y[7],
                           lo_ref.x[8], lo_ref.y[8], lo_ref.x[0], lo_ref.y[0], x[0], x[1]),
        axis=1)
    maze_arm_df['center'] = maze_arm_df.sum(axis=1) == 0
    return maze_arm_df


def maze_turn(maze_arm_df: pd.DataFrame):
    maze_arm_df.location.fillna(method='ffill', inplace=True)
    maze_arm_df.location.fillna(method='bfill', inplace=True)
    maze_arm_df['turn'] = maze_arm_df.location.diff(periods=-1)
    maze_arm_df.loc[maze_arm_df.turn == 0, 'turn'] = None
    turn_map = {-5: 'L', 3: 'R', 8: 'L', 5: 'R', -3: 'L', -8: 'R'}
    maze_arm_df.turn = maze_arm_df.turn.map(turn_map)
    return maze_arm_df


def Gram(Series, reminder=0, length=4):
    text = Series.str.cat()
    if length == 4:
        str_pattern = r'.{4}'
    elif length == 3:
        str_pattern = r'.{3}'
    gram = re.findall(str_pattern, text)
    if reminder == 1:
        gram.append(text[(len(gram) * length):])
    return gram


def maze_pattern(length: int == 4):
    if length == 4:
        step_length_map = {'LLLL': -8, 'LLLR': -7, 'LLRL': -6, 'LRLL': -5,
                           'RLLL': -4, 'LLRR': -3, 'LRRL': -2, 'LRLR': -1,
                           'RLRL': 1, 'RLLR': 2, 'RRLL': 3, 'LRRR': 4,
                           'RLRR': 5, 'RRLR': 6, 'RRRL': 7, 'RRRR': 8}
        strategies_index = {'bin': ['1-6', '1-6', '1-6', '1-6',
                                    '1-6', '1-6', '1-6', '1-6',
                                    '1-6', '1-6', '1-6', '1-6',
                                    '1-6', '1-6', '1-6', '1-6'],
                            'Sequence': ['LLLL', 'LLLR', 'LLRL', 'LRLL',
                                         'RLLL', 'LLRR', 'LRRL', 'LRLR',
                                         'RLRL', 'RLLR', 'RRLL', 'LRRR',
                                         'RLRR', 'RRLR', 'RRRL', 'RRRR'],
                            'frequence': [np.nan, np.nan, np.nan, np.nan,
                                          np.nan, np.nan, np.nan, np.nan,
                                          np.nan, np.nan, np.nan, np.nan,
                                          np.nan, np.nan, np.nan, np.nan]}
    elif length == 3:
        step_length_map = {'LLL': -4, 'LLR': -3, 'LRL': -2, 'RLL': -1,
                           'LRR': 1, 'RLR': 2, 'RRL': 3, 'RRR': 4}
        strategies_index = {'bin': ['1-6', '1-6', '1-6', '1-6',
                                    '1-6', '1-6', '1-6', '1-6'],
                            'Sequence': ['LLL', 'LLR', 'LRL', 'RLL',
                                         'LRR', 'RLR', 'RRL', 'RRR'],
                            'frequence': [np.nan, np.nan, np.nan, np.nan,
                                          np.nan, np.nan, np.nan, np.nan]}
    return step_length_map, strategies_index


def time_series_analysis_plot(data_plot: pd.Series):
    plt.figure(figsize=(20, 5.5))

    ax1 = plt.subplot(1, 3, 1)

    ax1.set_title('Time Series')
    ax1.set_xlabel('Time (Step)')
    ax1.set_ylabel('Step Length')

    ax1.grid(b=True, which='major')

    ax1.plot(data_plot)

    ax2 = plt.subplot(1, 3, 2)

    pd.plotting.lag_plot(data_plot, lag=1, ax=ax2)

    ax2.set_title('Lag Plot')
    ax2.set_xlabel('Lag Y(t)')
    ax2.set_ylabel('Y(t+1)')

    ax2.grid(b=True, which='major')

    ax3 = plt.subplot(1, 3, 3)

    ax3.set_title('Autocorrelation')
    ax3.set_xlabel('Lag (Step)')
    ax3.set_ylabel('ACF')

    ax3.grid(b=True, which='major')

    plot_acf(data_plot, lags=20, ax=ax3)

    return plt


def LimitSteps(cal_data_file, steps=40, pattern=4, info=1, ):
    if pattern == 4:
        strategies_index = {'Sequence': ['LLLL', 'LLLR', 'LLRL', 'LRLL', 'RLLL', 'LLRR', 'LRRL', 'LRLR',
                                         'RLRL', 'RLLR', 'RRLL', 'LRRR', 'RLRR', 'RRLR', 'RRRL', 'RRRR'],
                            'frequence': [0, 0, 0, 0, 0, 0, 0, 0,
                                          0, 0, 0, 0, 0, 0, 0, 0]}
    elif pattern == 3:
        strategies_index = {'Sequence': ['LLL', 'LLR', 'LRL', 'RLL',
                                         'LRR', 'RLR', 'RRL', 'RRR'],
                            'frequence': [0, 0, 0, 0,
                                          0, 0, 0, 0]}

    strategies_index = pd.DataFrame(strategies_index)
    strategies_index.drop(columns='frequence', inplace=True)

    cal_data_file = Path(cal_data_file)
    step_data = pd.read_excel(cal_data_file, sheet_name='step', usecols=['Sequence', 'Step'], index_col='Step')
    step_data = step_data.iloc[:steps, :]

    step_counts = step_data.Sequence.value_counts()
    step_counts = pd.DataFrame(step_counts)
    step_counts.reset_index(inplace=True)
    step_counts.columns = ['Sequence', 'frequence']

    results = pd.merge(strategies_index, step_counts, how='left', on='Sequence')
    results.fillna(value=0, inplace=True)
    results = results.pivot_table(index=None, columns='Sequence', values=['frequence'])

    if info == 1:
        filename = cal_data_file.stem
        str_pattern = re.compile(r'\d+')
        video_fish_num = filename.split('至鱼')[0]
        video_fish_num = int(re.findall(str_pattern, video_fish_num)[0])

        fish_order = filename.split(')-鱼')[1].split(' ')[0]
        fish_order = int(re.findall(str_pattern, fish_order)[0])

        fish_num = video_fish_num + fish_order - 1

        results.insert(0, 'fish_num', fish_num)
        results['filename'] = filename

    return results
