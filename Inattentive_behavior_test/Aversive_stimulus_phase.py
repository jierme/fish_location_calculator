from function import *
import os
from PIL import Image
import numpy as np

# %%
real_tank_xy = 74  # mm
fps = 6  # frame/s
time = 30 * 60  # video_time
total_frame = fps * time + 1
bin_length = 5  # mins

# %%
folder_path = Path(r'./imageJ_track_data/Aversive_stimulus_phase')

# %%
# Step0.
foldr_save = Path(r'/imageJ_track_data-results/Aversive_stimulus_phase')
if not foldr_save.exists():
    foldr_save.mkdir()

for root, dirs, files in os.walk(folder_path, topdown=False):
    for sub_foldr_name in dirs:
        subfolder_path = os.path.join(root, sub_foldr_name)
        subfolder_path = Path(subfolder_path)
        # Step1.
        print('Dealing：' + subfolder_path.name)
        csv_Results = pd.read_csv(subfolder_path / 'Results.csv', index_col=0)[['X', 'Y']]
        points_num = csv_Results.shape[0]
        fish_num = int(points_num / 2)

        # Step2.
        pic_0001s = subfolder_path.glob('*0001.jpg')
        for index_pic, pics in enumerate(pic_0001s):
            pic_path = pics
        pic = Image.open(pic_path)
        # print('W：%d,H：%d' % (pic.size[0], pic.size[1]))

        # Step3. lo-fish_index-i.csv
        all_fish_index_xy = pd.DataFrame()
        for fish_index in range(1, int(fish_num + 1)):
            print('Fish NO.', fish_index)

            lo_csv_pattern = 'lo-' + str(fish_index) + '-*.csv'
            fish_index_xy = lo_csvs_to_fishxy(path=subfolder_path, pattern=lo_csv_pattern, check=False)
            all_fish_index_xy = pd.concat([all_fish_index_xy, fish_index_xy], ignore_index=True)

            # Step4.
            tankxy = csv_Results.iloc[[(fish_index * 2 - 2), (fish_index * 2 - 1)]]
            video_tank_xy = math.sqrt(sum((tankxy.iloc[0] - tankxy.iloc[1]) ** 2))
            x1 = tankxy.iloc[0, 0]
            x2 = tankxy.iloc[1, 0]
            y1 = tankxy.iloc[0, 1]
            y2 = tankxy.iloc[1, 1]

            c_y = fish_index_xy.Y1.max()-2

            fish_index_xy_ffillna = fish_index_xy.fillna(method="ffill")
            fish_index_xy_inter = fish_index_xy.interpolate(method='linear',
                                                            axis=0,
                                                            limit=None,
                                                            inplace=False,
                                                            limit_direction=None,
                                                            limit_area=None)

            fish_index_xy_inter.loc[fish_index_xy_ffillna.Y1 > c_y] = np.nan

            fish_index_xy = fish_index_xy_inter

            new_xlsx_cal = fish_xy_cal(fish_index_xy, fps, video_tank_xy, real_tank_xy, bin_length=bin_length)

            new_xlsx_inf = pd.DataFrame()
            new_xlsx_inf_items = ['fps', 'vidDuration', 'calDuration', 'vidHeight', 'vidWidth',
                                  'mark1_x', 'mark1_y', 'mark2_x', 'mark2_y',
                                  'mark12_dis_pix', 'mark12_dis_mm']
            new_xlsx_inf_values = [fps, time, time, pic.size[1], pic.size[0],
                                   x1, y1, x2, y2,
                                   video_tank_xy, real_tank_xy]
            new_xlsx_inf_units = ['frame/s', 's', 's', 'pix', 'pix',
                                  'pix', 'pix', 'pix', 'pix',
                                  'pix', 'mm']

            new_xlsx_inf['items'] = new_xlsx_inf_items
            new_xlsx_inf['values'] = new_xlsx_inf_values
            new_xlsx_inf['units'] = new_xlsx_inf_units

            # Step 5. 计算sum表单中需要的参数
            # distance
            dis_real_mm_total = new_xlsx_cal.dis_frame_real_mm.sum()
            # duration
            duration_total = new_xlsx_cal.y.count() / fps


            subfolder_name = subfolder_path.name
            fish_nums = subfolder_name.split(' ')[0].split('-')[-2]
            stage = subfolder_name.split(' ')[0].split('-')[-1]
            new_xlsx_sum = pd.DataFrame({'fish_num': [fish_nums],
                                         'fish_order': [fish_index],
                                         'stage': [stage],
                                         'analysis_bin': ['total'],
                                         'dis_real_mm_total': [dis_real_mm_total],
                                         'duration_s_total': [duration_total],
                                         'filename': [subfolder_name]
                                         })

            new_xlsx_cal_temp = new_xlsx_cal.copy()
            new_xlsx_cal_temp = new_xlsx_cal_temp.drop([0])

            new_xlsx_sum_bin = pd.DataFrame()
            group_bins = new_xlsx_cal_temp.groupby(by='bin')
            for bin_index, group_bin in group_bins:
                # distance
                dis_real_mm_bin_total = group_bin.dis_frame_real_mm.sum()
                # duration
                duration_bin_total = group_bin.y.count() / fps

                new_xlsx_sum_bin = pd.DataFrame({'fish_num': [fish_nums],
                                                 'fish_order': [fish_index],
                                                 'stage': [stage],
                                                 'analysis_bin': [bin_index],
                                                 'dis_real_mm_total': [dis_real_mm_bin_total],
                                                 'duration_s_total': [duration_bin_total],
                                                 'filename': [subfolder_name]
                                                 })

                new_xlsx_sum = pd.concat([new_xlsx_sum, new_xlsx_sum_bin])

            # %% Step11.
            new_xlsx_file = foldr_save / (subfolder_path.name + '-Fish' + str(fish_index) + ' cal_data.xlsx')
            writer = pd.ExcelWriter(new_xlsx_file)

            new_xlsx_cal.to_excel(writer, sheet_name='cal', index=0)
            new_xlsx_inf.to_excel(writer, sheet_name='inf', index=0)
            new_xlsx_sum.to_excel(writer, sheet_name='sum', index=0)
            writer.save()

print('All files are finished.')
