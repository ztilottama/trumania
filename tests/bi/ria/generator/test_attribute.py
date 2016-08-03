from bi.ria.generator.attribute import *
from bi.ria.generator.relationship import Relationship


def test_set_and_read_values_in_attribute_should_be_equal():
    tested = Attribute(ids=["a", "z", "e", "d", "f"],
                       init_values=[10, 20, 30, 40, 50])

    assert tested.get_values(["a"]).tolist() == [10]
    assert tested.get_values(["a", "d", "z"]).tolist() == [10, 40, 20]

    # getting no id should return empty list
    assert tested.get_values([]).tolist() == []


def test_updated_and_read_values_in_attribute_should_be_equal():
    tested = TransientAttribute(
        ids=["a", "z", "e", "d", "f"],
        init_values= [10,   20,  30,  40,  50])

    tested.update(["z", "d"], [22, 44])

    # value of a should untouched
    assert tested.get_values(["a"]).tolist() == [10]

    # arbitrary order should not be impacted
    assert tested.get_values(["a", "d", "z"]).tolist() == [10, 44, 22]


def test_updated_by_operation_and_read_values_in_attribute_should_be_equal():
    tested = TransientAttribute(
        ids=["a", "z", "e", "d", "f"],
        init_values=[10,   20,  30,  40,  50])

    data = pd.DataFrame({"A": ["a", "e", "d"],
                         "source": [1000, 5000, 4000]}).set_index("A",drop=False)

    op = tested.ops.overwrite(copy_from_field="source")
    updated = op.transform(data)

    print tested._table
    # input data should not have been impacted
    assert data.equals(updated)

    # value of a should untouched
    assert tested.get_values(["d", "a", "e"]).tolist() == [4000, 1000, 5000]

    # arbitrary order should not be impacted
    assert tested.get_values(["a", "d", "z"]).tolist() == [1000, 4000, 20]


def test_initializing_attribute_from_relationship_must_have_a_value_for_all():

    oneto1= Relationship(name="tested", seed=1)
    oneto1.add_relations(from_ids=["a", "b", "c", "d", "e"],
                         to_ids=["ta", "tb", "tc", "td", "te"])

    attr = Attribute(relationship=oneto1)

    expected = pd.DataFrame({"value": ["ta", "tb", "tc", "td", "te"]},
                            index=["a", "b", "c", "d", "e"])

    attr._table.sort_index().equals(expected)
