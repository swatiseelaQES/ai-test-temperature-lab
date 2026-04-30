from src.score_tests import count_assertions, count_test_functions, is_syntax_valid, keyword_coverage


def test_scoring_detects_valid_test_code():
    code = '''
def test_example():
    response_json = {"bookingid": 1, "booking": {"firstname": "Jim"}}
    assert response_json["bookingid"] == 1
    assert response_json["booking"]["firstname"] == "Jim"
'''
    assert is_syntax_valid(code)
    assert count_test_functions(code) == 1
    assert count_assertions(code) == 2


def test_keyword_coverage_detects_nested_booking():
    code = 'assert response_json["booking"]["firstname"] == "Jim"'
    coverage = keyword_coverage(code)
    assert coverage["nested_booking"] is True
