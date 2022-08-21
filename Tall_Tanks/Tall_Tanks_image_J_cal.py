#!/usr/bin/env python
# coding=utf-8

from PIL import Image
import os
import math
from function import *

# %%
real_tank_dis = 135  # mm
fps = 10  # frame/s
time = 900  # video_time s
total_frame = fps * time + 1

dir_path = r'./imageJ_track_data'

# %%
for root, dirs, files in os.walk(dir_path, topdown=False):
    # for name in files:
    #     print(os.path.join(root, name))
    order = 0
    for sub_foldr_name in dirs:
        order = order + 1
        print("Foldr NO." + str(order) + "：" + "\n" + sub_foldr_name)

        fish_nums = sub_foldr_name.split(' ')[0].split('-')[-1]
        stage = sub_foldr_name.split('_')[0]
        # print("\n")

        # %% find .jpg
        sub_foldr_path = Path(os.path.join(root, sub_foldr_name))
        pic_0001s = sub_foldr_path.glob('* 0001.jpg')
        for index, pics in enumerate(pic_0001s):
            pic_path = pics
        pic = Image.open(pic_path)
        # print('W：%d,H：%d' % (pic.size[0], pic.size[1]))

        # %% Results.csv
        csv_Results = Path(os.path.join(root, sub_foldr_name, "Results.csv"))
        csv_Results = pd.read_csv(csv_Results, usecols=["X", "Y"])
        fish_size = int(csv_Results.shape[0] / 2)

        # %% cal
        for fish_index in range(1, fish_size + 1):

            print('Fish NO.', fish_index, '：')
            lo_csv_pattern = 'lo-' + str(fish_index) + '-*.csv'
            fish_index_xy = lo_csvs_to_fishxy(path=sub_foldr_path, pattern=lo_csv_pattern, check=True)
            fish_index_xy = fish_index_xy.loc[0:9000, :]

            new_xlsx_cal = pd.DataFrame()
            new_xlsx_inf = pd.DataFrame()
            new_xlsx_sum = pd.DataFrame()

            fishxy = fish_index_xy

            real_total_frame = fishxy.shape[0]

            if real_total_frame >= total_frame:
                fishxy = fishxy.iloc[0: total_frame]

            else:
                none_num = total_frame - real_total_frame
                none_df = pd.DataFrame({'X1': [pd.NaT],
                                        'Y1': [pd.NaT]})
                for add_num in range(none_num):
                    fishxy = fishxy.append(none_df)
                fishxy.reset_index(drop=True, inplace=True)
                fishxy.fillna(method='ffill', inplace=True)

            tankxy = csv_Results.iloc[[(fish_index * 2 - 2), (fish_index * 2 - 1)]]
            video_tankxy = math.sqrt(sum((tankxy.iloc[0] - tankxy.iloc[1]) ** 2))
            x1 = tankxy.iloc[0, 0]
            x2 = tankxy.iloc[1, 0]
            y1 = tankxy.iloc[0, 1]
            y2 = tankxy.iloc[1, 1]

            dis_frame_pix = 0
            dis_frame_pix_list = []
            for frame in range(0, total_frame - 1):
                dis_frame_pix = math.sqrt(sum((fishxy.iloc[frame] - fishxy.iloc[frame + 1]) ** 2))
                dis_frame_pix_list.append(dis_frame_pix)

            dis_frame_pix_list.insert(0, None)

            new_xlsx_cal['frame'] = range(0, total_frame)
            new_xlsx_cal['time'] = new_xlsx_cal.frame / fps
            new_xlsx_cal['x'] = fishxy.X1
            new_xlsx_cal['y'] = fishxy.Y1
            new_xlsx_cal['dis_frame_pix'] = dis_frame_pix_list
            new_xlsx_cal['location'] = fishxy.Y1

            new_xlsx_cal['dis_frame_real_mm'] = new_xlsx_cal.dis_frame_pix / video_tankxy * real_tank_dis
            new_xlsx_cal['speed_frame_mm/s'] = new_xlsx_cal.dis_frame_real_mm * fps

            y_1 = y1
            y_4 = y2
            y_2 = y_1 + (y_4 - y_1) / 3
            y_3 = y_1 + (y_4 - y_1) * 2 / 3

            new_xlsx_cal.location[fishxy.Y1 < y_2] = 'up'
            new_xlsx_cal.location[fishxy.Y1 > y_3] = 'down'
            new_xlsx_cal.location[(fishxy.Y1 >= y_2) & (fishxy.Y1 <= y_3)] = 'center'


            new_xlsx_inf_items = ['fps', 'vidDuration', 'calDuration', 'vidHeight', 'vidWidth',
                                  'mark1_x', 'mark1_y', 'mark2_x', 'mark2_y',
                                  'mark12_dis_pix', 'mark12_dis_mm']
            new_xlsx_inf_values = [fps, time, time, pic.size[1], pic.size[0],
                                   x1, y1, x2, y2,
                                   video_tankxy, real_tank_dis]
            new_xlsx_inf_units = ['frame/s', 's', 's', 'pix', 'pix',
                                  'pix', 'pix', 'pix', 'pix',
                                  'pix', 'mm']

            new_xlsx_inf['items'] = new_xlsx_inf_items
            new_xlsx_inf['values'] = new_xlsx_inf_values
            new_xlsx_inf['units'] = new_xlsx_inf_units

            # Step 5. sum

            new_xlsx_cal_00to05min = new_xlsx_cal.iloc[0: 5 * 60 * fps + 1, :]
            new_xlsx_cal_05to10min = new_xlsx_cal.iloc[5 * 60 * fps + 1: 10 * 60 * fps + 1, :]
            new_xlsx_cal_10to15min = new_xlsx_cal.iloc[10 * 60 * fps + 1: 15 * 60 * fps + 1, :]

            # 00to15min
            # distance
            sum_00to15min_dis_real_mm_total = new_xlsx_cal.dis_frame_real_mm.sum()
            sum_00to15min_dis_real_mm_up = new_xlsx_cal.dis_frame_real_mm[new_xlsx_cal.location == 'up'].sum()
            sum_00to15min_dis_real_mm_center = new_xlsx_cal.dis_frame_real_mm[new_xlsx_cal.location == 'center'].sum()
            sum_00to15min_dis_real_mm_down = new_xlsx_cal.dis_frame_real_mm[new_xlsx_cal.location == 'down'].sum()
            # duration
            sum_00to15min_duration_up = (new_xlsx_cal.location == 'up').sum() / fps
            sum_00to15min_duration_center = (new_xlsx_cal.location == 'center').sum() / fps
            sum_00to15min_duration_down = (new_xlsx_cal.location == 'down').sum() / fps

            # freezing_time
            new_xlsx_cal_temp_freezing_time = new_xlsx_cal[['time', 'dis_frame_real_mm', 'location']].copy()
            new_xlsx_cal_temp_freezing_time['time_sort'] = new_xlsx_cal_temp_freezing_time.time.map(
                lambda x: math.ceil(x))
            new_xlsx_cal_temp_freezing_time.dropna(subset=['dis_frame_real_mm'], inplace=True)
            sum_00to15min_freezing_s_total = (
                    new_xlsx_cal_temp_freezing_time.groupby('time_sort').sum().dis_frame_real_mm < 0.25).sum()

            # cross line
            location_map = {'up': 2, 'center': 0, 'down': -5}
            new_xlsx_cal_temp = new_xlsx_cal.copy()
            new_xlsx_cal_temp.location = new_xlsx_cal_temp.location.map(location_map)
            sum_00to15min_cross_count_Series = new_xlsx_cal_temp.location.diff()
            sum_00to15min_cross_up_line = (sum_00to15min_cross_count_Series.abs() == 2).sum()  # 上至中 + 中至上
            sum_00to15min_cross_down_line = (sum_00to15min_cross_count_Series.abs() == 5).sum()  # 中至下 + 下至中

            # 00to05min
            # distance
            sum_00to05min_dis_real_mm_total = new_xlsx_cal_00to05min.dis_frame_real_mm.sum()
            sum_00to05min_dis_real_mm_up = new_xlsx_cal_00to05min.dis_frame_real_mm[
                new_xlsx_cal_00to05min.location == 'up'].sum()
            sum_00to05min_dis_real_mm_center = new_xlsx_cal_00to05min.dis_frame_real_mm[
                new_xlsx_cal_00to05min.location == 'center'].sum()
            sum_00to05min_dis_real_mm_down = new_xlsx_cal_00to05min.dis_frame_real_mm[
                new_xlsx_cal_00to05min.location == 'down'].sum()
            # duration
            sum_00to05min_duration_up = (new_xlsx_cal_00to05min.location == 'up').sum() / fps
            sum_00to05min_duration_center = (new_xlsx_cal_00to05min.location == 'center').sum() / fps
            sum_00to05min_duration_down = (new_xlsx_cal_00to05min.location == 'down').sum() / fps
            # freezing_time
            new_xlsx_cal_00to05min_temp_freezing_time = new_xlsx_cal_00to05min[
                ['time', 'dis_frame_real_mm', 'location']].copy()
            new_xlsx_cal_00to05min_temp_freezing_time['time_sort'] = new_xlsx_cal_00to05min_temp_freezing_time.time.map(
                lambda x: math.ceil(x))
            new_xlsx_cal_00to05min_temp_freezing_time.dropna(subset=['dis_frame_real_mm'], inplace=True)
            sum_00to05min_freezing_s_total = (
                    new_xlsx_cal_00to05min_temp_freezing_time.groupby('time_sort').sum().dis_frame_real_mm < 0.25).sum()

            # 分界线穿越次数
            location_map = {'up': 2, 'center': 0, 'down': -5}
            new_xlsx_cal_00to05min_temp = new_xlsx_cal_00to05min
            new_xlsx_cal_00to05min_temp.location = new_xlsx_cal_00to05min_temp.location.map(location_map)
            sum_00to05min_cross_count_Series = new_xlsx_cal_00to05min_temp.location.diff()
            sum_00to05min_cross_up_line = (sum_00to05min_cross_count_Series.abs() == 2).sum()  # 上至中 + 中至上
            sum_00to05min_cross_down_line = (sum_00to05min_cross_count_Series.abs() == 5).sum()  # 中至下 + 下至中

            # 05to10min
            # distance
            sum_05to10min_dis_real_mm_total = new_xlsx_cal_05to10min.dis_frame_real_mm.sum()
            sum_05to10min_dis_real_mm_up = new_xlsx_cal_05to10min.dis_frame_real_mm[
                new_xlsx_cal_05to10min.location == 'up'].sum()
            sum_05to10min_dis_real_mm_center = new_xlsx_cal_05to10min.dis_frame_real_mm[
                new_xlsx_cal_05to10min.location == 'center'].sum()
            sum_05to10min_dis_real_mm_down = new_xlsx_cal_05to10min.dis_frame_real_mm[
                new_xlsx_cal_05to10min.location == 'down'].sum()
            # duration
            sum_05to10min_duration_up = (new_xlsx_cal_05to10min.location == 'up').sum() / fps
            sum_05to10min_duration_center = (new_xlsx_cal_05to10min.location == 'center').sum() / fps
            sum_05to10min_duration_down = (new_xlsx_cal_05to10min.location == 'down').sum() / fps
            # freezing_time
            new_xlsx_cal_05to10min_temp_freezing_time = new_xlsx_cal_05to10min[
                ['time', 'dis_frame_real_mm', 'location']].copy()
            new_xlsx_cal_05to10min_temp_freezing_time['time_sort'] = new_xlsx_cal_05to10min_temp_freezing_time.time.map(
                lambda x: math.ceil(x))
            new_xlsx_cal_05to10min_temp_freezing_time.dropna(subset=['dis_frame_real_mm'], inplace=True)
            sum_05to10min_freezing_s_total = (
                    new_xlsx_cal_05to10min_temp_freezing_time.groupby('time_sort').sum().dis_frame_real_mm < 0.25).sum()

            #
            location_map = {'up': 2, 'center': 0, 'down': -5}
            new_xlsx_cal_05to10min_temp = new_xlsx_cal_05to10min
            new_xlsx_cal_05to10min_temp.location = new_xlsx_cal_05to10min_temp.location.map(location_map)
            sum_05to10min_cross_count_Series = new_xlsx_cal_05to10min_temp.location.diff()
            sum_05to10min_cross_up_line = (sum_05to10min_cross_count_Series.abs() == 2).sum()  # 上至中 + 中至上
            sum_05to10min_cross_down_line = (sum_05to10min_cross_count_Series.abs() == 5).sum()  # 中至下 + 下至中

            # 10to15min
            # distance
            sum_10to15min_dis_real_mm_total = new_xlsx_cal_10to15min.dis_frame_real_mm.sum()
            sum_10to15min_dis_real_mm_up = new_xlsx_cal_10to15min.dis_frame_real_mm[
                new_xlsx_cal_10to15min.location == 'up'].sum()
            sum_10to15min_dis_real_mm_center = new_xlsx_cal_10to15min.dis_frame_real_mm[
                new_xlsx_cal_10to15min.location == 'center'].sum()
            sum_10to15min_dis_real_mm_down = new_xlsx_cal_10to15min.dis_frame_real_mm[
                new_xlsx_cal_10to15min.location == 'down'].sum()
            # duration
            sum_10to15min_duration_up = (new_xlsx_cal_10to15min.location == 'up').sum() / fps
            sum_10to15min_duration_center = (new_xlsx_cal_10to15min.location == 'center').sum() / fps
            sum_10to15min_duration_down = (new_xlsx_cal_10to15min.location == 'down').sum() / fps
            # freezing_time
            new_xlsx_cal_10to15min_temp_freezing_time = new_xlsx_cal_10to15min[
                ['time', 'dis_frame_real_mm', 'location']].copy()
            new_xlsx_cal_10to15min_temp_freezing_time['time_sort'] = new_xlsx_cal_10to15min_temp_freezing_time.time.map(
                lambda x: math.ceil(x))
            new_xlsx_cal_10to15min_temp_freezing_time.dropna(subset=['dis_frame_real_mm'], inplace=True)
            sum_10to15min_freezing_s_total = (
                    new_xlsx_cal_10to15min_temp_freezing_time.groupby('time_sort').sum().dis_frame_real_mm < 0.25).sum()

            #
            location_map = {'up': 2, 'center': 0, 'down': -5}
            new_xlsx_cal_10to15min_temp = new_xlsx_cal_10to15min
            new_xlsx_cal_10to15min_temp.location = new_xlsx_cal_10to15min_temp.location.map(location_map)
            sum_10to15min_cross_count_Series = new_xlsx_cal_10to15min_temp.location.diff()
            sum_10to15min_cross_up_line = (sum_10to15min_cross_count_Series.abs() == 2).sum()
            sum_10to15min_cross_down_line = (sum_10to15min_cross_count_Series.abs() == 5).sum()

            # %%
            new_xlsx_sum = pd.DataFrame({'fish_num': [fish_nums, fish_nums, fish_nums, fish_nums],
                                         'fish_order': [fish_index, fish_index, fish_index, fish_index],
                                         'stage': [stage, stage, stage, stage],
                                         'analysis_time': ['00to05min', '05to10min', '10to15min', '00to15min'],
                                         'dis_real_mm_total': [sum_00to05min_dis_real_mm_total,
                                                               sum_05to10min_dis_real_mm_total,
                                                               sum_10to15min_dis_real_mm_total,
                                                               sum_00to15min_dis_real_mm_total],
                                         'dis_real_mm_up': [sum_00to05min_dis_real_mm_up,
                                                            sum_05to10min_dis_real_mm_up,
                                                            sum_10to15min_dis_real_mm_up,
                                                            sum_00to15min_dis_real_mm_up],
                                         'dis_real_mm_center': [sum_00to05min_dis_real_mm_center,
                                                                sum_05to10min_dis_real_mm_center,
                                                                sum_10to15min_dis_real_mm_center,
                                                                sum_00to15min_dis_real_mm_center],
                                         'dis_real_mm_down': [sum_00to05min_dis_real_mm_down,
                                                              sum_05to10min_dis_real_mm_down,
                                                              sum_10to15min_dis_real_mm_down,
                                                              sum_00to15min_dis_real_mm_down],
                                         'duration_s_up': [sum_00to05min_duration_up,
                                                           sum_05to10min_duration_up,
                                                           sum_10to15min_duration_up,
                                                           sum_00to15min_duration_up],
                                         'duration_s_center': [sum_00to05min_duration_center,
                                                               sum_05to10min_duration_center,
                                                               sum_10to15min_duration_center,
                                                               sum_00to15min_duration_center],
                                         'duration_s_down': [sum_00to05min_duration_down,
                                                             sum_05to10min_duration_down,
                                                             sum_10to15min_duration_down,
                                                             sum_00to15min_duration_down],
                                         'cross_line_up': [sum_00to05min_cross_up_line,
                                                           sum_05to10min_cross_up_line,
                                                           sum_10to15min_cross_up_line,
                                                           sum_00to15min_cross_up_line],
                                         'cross_line_down': [sum_00to05min_cross_down_line,
                                                             sum_05to10min_cross_down_line,
                                                             sum_10to15min_cross_down_line,
                                                             sum_00to15min_cross_down_line],
                                         'freezing_s_total': [sum_00to05min_freezing_s_total,
                                                              sum_05to10min_freezing_s_total,
                                                              sum_10to15min_freezing_s_total,
                                                              sum_00to15min_freezing_s_total],
                                         'filename': [sub_foldr_name, sub_foldr_name, sub_foldr_name, sub_foldr_name]
                                         })

            # Step 6.
            foldr_save = Path(dir_path).parent / (Path(dir_path).stem + '-results')
            if not foldr_save.exists():
                foldr_save.mkdir()

            new_xlsx_file = foldr_save / (sub_foldr_name + ' Fish' + str(fish_index) + ' cal_data.xlsx')
            writer = pd.ExcelWriter(new_xlsx_file)
            new_xlsx_cal.to_excel(writer, sheet_name='cal', index=0)
            new_xlsx_inf.to_excel(writer, sheet_name='inf', index=0)
            new_xlsx_sum.to_excel(writer, sheet_name='sum', index=0)
            writer.save()
            print('Fish NO.' + str(fish_index) + ', Finished.')
        print('Finished：' + sub_foldr_name)

print('All folders finished.')
