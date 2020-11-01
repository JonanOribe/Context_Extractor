from main_utils import dataframe_percent_and_points, text_cleaner

def test_text_cleaner():
    web_content='_This_* is a good place to start messing up thing like  #__!'
    assertion_value=text_cleaner(web_content).rstrip()
    example_text=' This   is a good place to start messing up thing like  '.rstrip()
    assert assertion_value == example_text and assertion_value != web_content

def test_dataframe_percent_and_points():
    df_len_1,df_len_2=30,36
    points_ranges,points_ranges_2=dataframe_percent_and_points(df_len_1),dataframe_percent_and_points(df_len_2)
    assert (max(points_ranges[0]) == 2) and (max(points_ranges[1]) == 5) and (max(points_ranges[2]) == 8) and (max(points_ranges[3]) != 10)
    assert (max(points_ranges_2[0]) == 3) and (max(points_ranges_2[1]) == 6) and (max(points_ranges_2[2]) == 10) and (max(points_ranges_2[3]) != 15)
