from main_utils import dataframe_percent_and_points, text_cleaner

def test_text_cleaner():
    web_content='_This_* is a good place to start messing up thing like  #__!'
    assertion_value=text_cleaner(web_content).rstrip()
    example_text=' This   is a good place to start messing up thing like  '.rstrip()
    assert assertion_value == example_text
    assert assertion_value != web_content

def test_dataframe_percent_and_points():
    df_len_1=30
    df_len_2=36
    first_slice,second_slice,third_slice=dataframe_percent_and_points(df_len_1)
    first_slice_2,second_slice_2,third_slice_2=dataframe_percent_and_points(df_len_2)
    assert first_slice == 3
    assert second_slice == 6
    assert third_slice == 9
    assert third_slice != 10
    assert first_slice_2 == 4
    assert second_slice_2 == 7
    assert third_slice_2 == 11
    assert third_slice_2 != 15
