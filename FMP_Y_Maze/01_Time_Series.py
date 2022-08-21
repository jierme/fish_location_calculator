from function import *
# %%
folder = Path(r'./imageJ_track_data-results')
step_limit = 50

# %%
cal_data_file_list = folder.glob('* cal_data.xlsx')

# Step0. Create a folder to store the results
foldr_save = folder.parent / (folder.name + '-time_series-step_limit_to_' + str(step_limit))
if not foldr_save.exists():
    foldr_save.mkdir()

# Step1. plot
error_list = []
for file in cal_data_file_list:
    cal_data = pd.read_excel(file, sheet_name='step')
    cal_data = cal_data.iloc[0:step_limit, :]

    time_series_plot_path = foldr_save / (file.stem + ' -time_series.svg')

    try:
        time_series_plot = time_series_analysis_plot(cal_data.cumulative_sum_lengths)
        time_series_plot.savefig(time_series_plot_path, format='svg', dpi=1000)
        time_series_plot.show()

    except Exception as e:
        error = file.stem
        error_list.append(error)
        print(file.stem + 'Error，pass')
        pass
    continue

print('Error:')
for element in error_list:
    print(element)

error_list_path = foldr_save / 'error_list.csv'
error_list = pd.DataFrame(error_list)
error_list.to_csv(error_list_path, index=False, encoding='utf-8')
