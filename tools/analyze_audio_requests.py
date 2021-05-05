import pandas

def top_languages(requests_df):
    requests_df['count'] = 1
    grouped_df = requests_df.groupby('language_code').agg({'count': 'sum'}).reset_index()
    grouped_df = grouped_df.sort_values('count', ascending=False)
    print(grouped_df)
    

def top_voices(requests_df):
    requests_df['count'] = 1
    grouped_df = requests_df.groupby(['service', 'language_code', 'voice_key']).agg({'count': 'sum'}).reset_index()
    grouped_df = grouped_df.sort_values('count', ascending=False)
    print(grouped_df.head(50))    

def find_duplicates(requests_df):
    requests_df['count'] = 1
    
    # grouped_df = requests_df.groupby(['text', 'language_code']).agg({'count': 'sum'}).reset_index()

    # group_by = ['text', 'language_code', 'service', 'voice_key', 'options']
    group_by = ['text', 'language_code']

    grouped_df = requests_df.groupby(group_by).agg({'count': 'sum'}).reset_index()
    grouped_df = grouped_df[grouped_df['count'] > 1]
    grouped_df = grouped_df.sort_values('count', ascending=False)

    print(grouped_df.head(50))
    # print(grouped_df['dup_characters'].sum())

def find_request(requests_df):
    text = 'mouiller'
    subset_df = requests_df[requests_df['text'] == text]
    print(subset_df)


def load_requests():
    requests_df = pandas.read_csv('temp_data_files/audio_requests.csv')
    # print(requests_df)
    top_languages(requests_df)
    # top_voices(requests_df)
    # find_duplicates(requests_df)
    # find_request(requests_df)



if __name__ == '__main__':
    load_requests()