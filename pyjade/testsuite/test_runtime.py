from pyjade import runtime


class TestIteration(object):

    def test_it_returns_mappings_unaltered(self):
        mapping = {}
        assert runtime.iteration(mapping, 1) is mapping

    def test_it_returns_empty_list_on_empty_input(self):
        l = iter([])
        assert list(runtime.iteration(l, 1)) == []

    def test_it_iterates_as_is_if_numkeys_is_same_as_cardinality(self):
        l = [(1, 2), (3, 4)]
        assert list(runtime.iteration(l, 2)) == l

    def test_it_extends_with_index_if_items_are_iterable(self):
        l = [('a',), ('b',)]
        assert list(runtime.iteration(l, 2)) == [('a', 0), ('b', 1)]

    def test_it_adds_index_if_items_are_strings(self):
        l = ['a', 'b']
        assert list(runtime.iteration(l, 2)) == [('a', 0), ('b', 1)]

    def test_it_adds_index_if_items_are_non_iterable(self):
        l = [1, 2]
        assert list(runtime.iteration(l, 2)) == [(1, 0), (2, 1)]

    def test_it_doesnt_swallow_first_item_of_iterators(self):
        l = [1, 2]
        iterator = iter(l)
        assert list(runtime.iteration(iterator, 1)) == l
