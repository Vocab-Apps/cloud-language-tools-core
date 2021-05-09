

import pandas


voices_df = pandas.read_json('temp_data_files/voicelist.json')

voices_df = voices_df[voices_df['service'] == 'CereProc']
voices_df['count'] = 1

grouped_df = voices_df.groupby('audio_language_name').agg({'count': 'sum'}).reset_index()
grouped_df = grouped_df.sort_values('count', ascending=False)
print(grouped_df)

# print(voices_df)