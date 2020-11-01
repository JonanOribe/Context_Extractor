from main_utils import text_cleaner

web_content='_This_* is a good place to start messing up thing like  #__!'

def test_text_cleaner():
    assertion_value=text_cleaner(web_content).rstrip()
    example_text=' This   is a good place to start messing up thing like  '.rstrip()
    assert assertion_value == example_text
    assert assertion_value != web_content
