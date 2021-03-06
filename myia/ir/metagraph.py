"""Graph generation from number of arguments or type signatures."""


from ..dtype import ismyiatype
from ..prim.py_implementations import issubtype, typeof


class GraphGenerationError(Exception):
    """Raised when a graph could not be generated by a MetaGraph."""


class MetaGraph:
    """Graph generator.

    Can be called with a pipeline's resources and a list of argument types to
    generate a graph corresponding to these types.
    """

    def __init__(self, name):
        """Initialize a MetaGraph."""
        self.name = name
        self.cache = {}

    def normalize_args(self, args):
        """Return normalized versions of the arguments.

        By default, this returns args unchanged.
        """
        return args

    def generate_graph(self, args):
        """Generate a Graph for the given abstract arguments."""
        from ..abstract.utils import build_type
        types = tuple([build_type(arg) for arg in args])
        if types not in self.cache:
            self.cache[types] = self.generate_from_types(types)
        return self.cache[types]

    def generate_from_types(self, types):
        """Generate a Graph for this type signature."""
        raise NotImplementedError(
            'Override generate_from_types in subclass.'
        )

    def __str__(self):
        return self.name


class MultitypeGraph(MetaGraph):
    """Associates type signatures to specific graphs."""

    def __init__(self, name, entries={}):
        """Initialize a MultitypeGraph."""
        super().__init__(name)
        self.entries = list(entries.items())

    def register(self, *types):
        """Register a function for the given type signature."""
        def deco(fn):
            self.entries.append((types, fn))
            return fn
        return deco

    def _getfn(self, types):
        for sig, fn in self.entries:
            if len(sig) != len(types):
                continue
            if all(issubtype(t2, t1) if ismyiatype(t1) else isinstance(t2, t1)
                   for t1, t2 in zip(sig, types)):
                return fn
        else:
            raise GraphGenerationError(types)

    def generate_from_types(self, types):
        """Generate a Graph for this type signature."""
        from ..parser import parse
        return parse(self._getfn(types))

    def __call__(self, *args):
        """Call like a normal function."""
        fn = self._getfn([typeof(arg) for arg in args])
        return fn(*args)
