from function import *
from PIL import Image
import os

real_tank_xy = 12  # The width of the arm (outer diameter)mm
fps = 6  # frame/s
length = 4  # turns

folder_path = Path('./imageJ_track_data')

# Step0. Create a folder to store the results
foldr_save = folder_path.parent / (folder_path.name + '-results')
if not foldr_save.exists():
    foldr_save.mkdir()

for root, dirs, files in os.walk(folder_path, topdown=False):
    for sub_foldr_name in dirs:
        subfolder_path = os.path.join(root, sub_foldr_name)
        subfolder_path = Path(subfolder_path)
        # Step1. Determine how many fish there are
        print('Dealing：' + subfolder_path.name)
        csv_Results = pd.read_csv(subfolder_path / 'Results.csv', index_col=0)[['X', 'Y']]
        points_num = csv_Results.shape[0]
        fish_num = int(points_num / 9)
        print('There are', fish_num, 'fish')

        # Step2. Find .jpg
        pic_0001s = subfolder_path.glob('*0001.jpg')
        for index_pic, pics in enumerate(pic_0001s):
            pic_path = pics
        pic = Image.open(pic_path)
        # print('Width：%d,Height：%d' % (pic.size[0], pic.size[1]))

        # Step3. Find all location files 'lo-fish_index-i.csv'
        all_fish_index_xy = pd.DataFrame()
        for fish_index in range(1, int(fish_num + 1)):
            print('Fish NO.', fish_index, ':')
            # Step4. ('X1', 'Y1')
            lo_csv_pattern = 'lo-' + str(fish_index) + '-*.csv'
            fish_index_xy = lo_csvs_to_fishxy(path=subfolder_path, pattern=lo_csv_pattern, check=True)
            fish_index_xy = fish_index_xy.loc[0:21600, :]
            all_fish_index_xy = pd.concat([all_fish_index_xy, fish_index_xy], ignore_index=True)

            # Step7. Positioning information
            lo_ref = lo_Results(csv_Results, fish_index)

            # Step8. Cal
            # Step8.1 Tank pixel size
            video_tank_xy = (dis_points(lo_ref.x[1], lo_ref.y[1], lo_ref.x[2], lo_ref.y[2]) +
                             dis_points(lo_ref.x[4], lo_ref.y[4], lo_ref.x[5], lo_ref.y[5]) +
                             dis_points(lo_ref.x[7], lo_ref.y[7], lo_ref.x[8], lo_ref.y[8])) / 3
            # Step8.2 Pixel movement distance
            new_xlsx_cal = fish_xy_cal(fish_index_xy, fps, video_tank_xy, real_tank_xy)

            new_xlsx_cal['location'] = fish_index_xy.Y1
            new_xlsx_cal['turn'] = fish_index_xy.Y1

            # Step9. Determine which maze arm the fish is in (each frame)
            maze_arm_df = maze_arm(fish_index_xy, lo_ref)
            new_xlsx_cal['location'] = fish_index_xy.Y1
            new_xlsx_cal.loc[maze_arm_df['arm_0'] == True, 'location'] = 0
            new_xlsx_cal.loc[maze_arm_df['arm_5'] == True, 'location'] = 5
            new_xlsx_cal.loc[maze_arm_df['arm_-3'] == True, 'location'] = -3
            new_xlsx_cal.loc[maze_arm_df['center'] == True, 'location'] = None

            # Step10. Turns
            maze_arm_df['location'] = new_xlsx_cal.location.copy()
            # Step10.1
            maze_arm_df = maze_turn(maze_arm_df)

            # Step10.2
            new_xlsx_cal.loc[:, 'turn'] = maze_arm_df.turn.copy()
            new_xlsx_step = pd.DataFrame()
            new_xlsx_step[['frame', 'time(s)', 'time(minute)', 'bin', 'turn']] = \
                new_xlsx_cal[['frame', 'time(s)', 'time(minute)', 'bin', 'turn']].copy()
            new_xlsx_step.dropna(inplace=True)

            # Step10.3 Global
            global_step = pd.DataFrame()
            global_strategies = pd.DataFrame()
            step_length_map, strategies_index_1to6 = maze_pattern(length=length)

            global_step['Sequence'] = Gram(new_xlsx_step.turn, length=length)
            global_step.insert(0, 'Step', global_step.index + 1)

            global_step['Step_Length'] = global_step['Sequence'].map(step_length_map)
            global_step['cumulative_sum_lengths'] = global_step['Step_Length'].cumsum()

            global_strategies['frequence'] = global_step.Sequence.value_counts()
            global_strategies.sort_index(inplace=True, ascending=True)
            global_strategies.insert(0, 'Sequence', global_strategies.index)
            global_strategies.reset_index(drop=True, inplace=True)
            global_strategies.insert(0, 'bin', '1-6')

            # Step10.4
            group_sets = new_xlsx_step.loc[:, ['bin', 'turn']].groupby('bin')
            tetragram = group_sets.apply(
                lambda x: pd.DataFrame(Gram(x['turn'], length=length)))

            if tetragram.empty:
                im_strategies = pd.DataFrame()
            else:
                tetragram.columns = ['Sequence']
                tetragram.reset_index(inplace=True)
                tetragram.drop('level_1', axis=1, inplace=True)

                group_sets = tetragram.groupby('bin')
                im_strategies = tetragram['Sequence'].groupby(tetragram['bin']).value_counts()
                im_strategies = pd.DataFrame(im_strategies)
                im_strategies.columns = ['frequence']
                im_strategies.reset_index(inplace=True)


            strategies_index_1to6 = pd.DataFrame(strategies_index_1to6)

            strategies_index = pd.DataFrame()
            for i in range(1, 7):
                strategies_index_i = strategies_index_1to6.copy()
                strategies_index_i.bin = i
                strategies_index = pd.concat([strategies_index, strategies_index_i], ignore_index=True)
            strategies_index = pd.concat([strategies_index, strategies_index_1to6], ignore_index=True)


            all_strategies = pd.concat([im_strategies, global_strategies], ignore_index=True)
            strategies = strategies_index.copy()
            strategies = pd.merge(strategies_index, all_strategies, on=['bin', 'Sequence'], how='outer')

            strategies.frequence_x.fillna(strategies.frequence_y, inplace=True)
            strategies = strategies.drop(['frequence_y'], axis=1)
            strategies.rename(columns={"frequence_x": "frequence"}, inplace=True)

            # pivot
            new_xlsx_strategies = strategies.pivot(index='bin', columns='Sequence', values='frequence')
            new_xlsx_strategies.fillna(value=0, inplace=True)


            subfolder_name = subfolder_path.name
            subfolder_name_fish_num = subfolder_name.split(' ')[0].split('-')[-1]

            new_xlsx_strategies.insert(0, 'bin', new_xlsx_strategies.index)
            new_xlsx_strategies.insert(0, 'fish_order', fish_index)
            new_xlsx_strategies.insert(0, 'fish_num', subfolder_name_fish_num)

            new_xlsx_strategies_dis = new_xlsx_cal[['bin', 'dis_frame_real_mm']].groupby('bin').sum()
            new_xlsx_strategies_dis.drop([0], inplace=True)
            new_xlsx_strategies_dis.loc['1-6'] = new_xlsx_strategies_dis.sum()
            new_xlsx_strategies_dis.index = [1, 2, 3, 4, 5, 6, '1-6']
            new_xlsx_strategies['dis_frame_real_mm'] = new_xlsx_strategies_dis
            new_xlsx_strategies['filename'] = subfolder_name


            new_xlsx_file = foldr_save / (subfolder_path.name + '-Fish' + str(fish_index) + ' cal_data.xlsx')
            writer = pd.ExcelWriter(new_xlsx_file)

            new_xlsx_cal.to_excel(writer, sheet_name='cal', index=0)
            global_step.to_excel(writer, sheet_name='step', index=0)
            new_xlsx_strategies.to_excel(writer, sheet_name='strategies', index=0)
            writer.save()

        # Step12. heatmap
            fish_index_heat_map_path = foldr_save / (subfolder_path.name + '-Fish' + str(fish_index) + ' -heat_map.svg')
            fish_index_heat_map = maze_heatmap(fish_index_xy.X1, fish_index_xy.Y1, pic_path=pic_path)
            fish_index_heat_map.savefig(fname=fish_index_heat_map_path, format="svg")
            fish_index_heat_map.show()
            print('Fish NO.', fish_index, ', Finished')


        all_fish_index_heat_map_path = foldr_save / (subfolder_path.name + ' -heat_map.svg')
        all_fish_index_heat_map = maze_heatmap(all_fish_index_xy.X1, all_fish_index_xy.Y1, pic_path=pic_path)
        all_fish_index_heat_map.savefig(fname=all_fish_index_heat_map_path, format="svg")
        print('ALl in One：')
        all_fish_index_heat_map.show()

        print(subfolder_path.name, '，Finished.')

print('All files are finished.')
