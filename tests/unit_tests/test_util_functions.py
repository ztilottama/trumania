from datagenerator.util_functions import *


def test_merge_two_empty_dict_should_return_empty_dict():
    assert {} == merge_2_dicts({}, {})


def test_merge_two_none_dict_should_return_empty_dict():
    assert {} == merge_2_dicts(None, None)


def test_merging_one_dict_with_none_should_yield_dict():
    d1 = {"a": 1, "b": 2}
    assert d1 == merge_2_dicts(d1, None)


def test_merging_none_with_one_dict_should_yield_dict():
    d2 = {"a": 1, "b": 2}
    assert d2 == merge_2_dicts(None, d2)


def test_merge_empty_with_dict_should_return_itself():

    d1 = {"a": 1, "b": 2}
    assert d1 == merge_2_dicts(d1, {})
    assert d1 == merge_2_dicts({}, d1)


def test_merge_non_overlapping_dict_should_return_all_values():

    d1 = {"a": 1, "b": 2}
    d2 = {"c": 3, "d": 4}
    assert {"a": 1, "b": 2, "c": 3, "d": 4} == merge_2_dicts(d1, d2)


def test_merge_dict_to_itself_should_return_doubled_values():

    d1 = {"a": 1, "b": 2}
    assert {"a": 2, "b": 4} == merge_2_dicts(d1, d1, lambda a, b: a+b)


def test_merging_one_dictionary_should_yield_itself():
    d1 = {"a": 1, "b": 2}
    assert d1 == merge_dicts([d1], lambda a, b: a+b)


def test_merging_an_empty_list_of_dicts_should_yield_empty_dict():
    assert {} == merge_dicts([])


def test_merging_an_empty_gen_of_dicts_should_yield_empty_dict():
    emtpy_gen = ({"a": 1} for _ in [])
    assert {} == merge_dicts(emtpy_gen)


def test_merging_many_dictionary_should_yield_expected_result():
    d1 ={"a": 10, "b": 20}
    d2 ={"a": 100, "c": 30}
    d3 ={}
    d4 ={"b": 200, "z": 1000}
    d5 = {"z": -10}

    merged = merge_dicts([d1, d2, d3, d4, d5], lambda a, b: a+b)

    assert {"a": 110, "b": 220, "c": 30, "z": 990} == merged


def test_merging_many_dictionary_from_gen_should_yield_expected_result():
    ds = [{"a": 10, "b": 20},
          {"a": 100, "c": 30},
          {},
          {"b": 200, "z": 1000},
          {"z": -10}]

    dicts_gens = (d for d in ds)

    merged = merge_dicts(dicts_gens, lambda a, b: a+b)

    assert {"a": 110, "b": 220, "c": 30, "z": 990} == merged


def test_is_sequence():
    assert is_sequence([])
    assert is_sequence([1, 2, 3, 1])
    assert is_sequence({1, 2, 3, 1})
    assert not is_sequence(1)
    assert not is_sequence("hello")

