import unittest
from ..parser import parse_output_spec, parse_embedded_spec, EmbeddedSpecParser, ParseException
from ..input import InputSpecification


class TestParser(unittest.TestCase):

    def test_valid_input_spec(self):
        valid_input_specs = [
            'INPUT(){}',
            'INPUT(x){}',
            'INPUT(){p();}',
            '''
                INPUT (
                    a,
                    obj,
                    nodes,          % comments are supported inside the spec, too
                ) {
                    empty();
                    simple(obj);
                    p(nodes[1].label);
                    node(n.label) for n in set nodes;
                    edge(n.label, m.label, m.prop[3]) for n in nodes for (i, m) in sequence n.neighbors;
                }
            ''',
        ]
        for valid_input_spec in valid_input_specs:
            try:
                spec = InputSpecification.parse(valid_input_spec)
                self.assertTrue(isinstance(spec, InputSpecification))
            except ParseException as e:
                self.fail("Error while parsing " + repr(valid_input_spec) + ": " + str(e))

    def test_invalid_input_spec(self):
        invalid_input_specs = [
            'INPUT { }',  # no argument list
            'INPUT ( )',  # no body
            'INPUT (x,y,z) { p(x, y) q(z) }',  # no semicolon after predicates
        ]
        # TODO: Tests for invalid variable bindings (with assertRaises(UndefinedVariableError) etc.)
        for invalid_input_spec in invalid_input_specs:
            with self.assertRaises(ParseException):
                InputSpecification.parse(invalid_input_spec)

    def test_valid_output_spec(self):
        valid_output_specs = [
            'OUTPUT{}',
            'OUTPUT{simple_nodes=set{node}}',
            'OUTPUT{static_object=SomeClass()}',
            '''
                OUTPUT {
                    % a comment about the output
                    colored_tuples = sequence {
                        predicate: color(X, C, I);
                        index: I;
                        content: (X, C);
                    }
                    colored_nodes = sequence {
                        predicate: color(X, C, I);
                        index: I;
                        content: ColoredNode(X, C);
                    }
                    graph = mypackage.mymodule.Graph(colored_nodes)
                    graph2 = mypackage.mymodule.Graph2(
                        set { predicate: vertex(X); content: (X); },
                        set { arc },
                        mypackage.mymodule.Blah(colored_nodes),
                        colored_tuples,
                    )
                    new_nodes = set {
                        predicate:
                            node(X),
                            color(X, C),
                            value(X, V);
                        content: Node(X, C, V);
                    }
                }
            ''',
        ]
        for valid_output_spec in valid_output_specs:
            try:
                parse_output_spec(valid_output_spec)
            except ParseException as e:
                self.fail("Error while parsing " + repr(valid_output_spec) + ": " + str(e))

    def test_invalid_output_spec(self):
        pass  # TODO

    def test_embedded_parser(self):
        valid_embedded_specs = [
            '',
            '% blah\n%! ',
            '%!  ',
            '%! INPUT(){}  OUTPUT{}',
            '''
                % This is some ASP code with I/O specs
                %! INPUT (xs) {
                %!  p(x) for x in xs;  % a comment inside the spec, should be ignored
                %! }
                q(X) :- p(X).  % bla blah   %! a spec marker inside an ASP comment should be ignored
                q(123). %! OUTPUT{}
            '''
        ]
        for valid_embedded_spec in valid_embedded_specs:
            try:
                parse_embedded_spec(valid_embedded_spec)
            except ParseException as e:
                self.fail("Error while parsing " + repr(valid_embedded_spec) + ": " + str(e))

    def test_embedded_parser_regex(self):
        result = EmbeddedSpecParser.extractFromString("""
            % a normal asp comment
            % another asp comment  %! this should be IGNORED
            p(abc).    % comment behind predicate
            p(xyz1).
            %! this is what we want to parse
            p(def).   %! behind predicate % IGNORED % IGNORED too
            p("quoted %!\\"string").  %! behind a quoted string containing percent
            q(X):-p(X).
            p("quoted"). % q("quoted but in comment").  %! means: this should be IGNORED.
        """)
        self.assertEqual(result, '\n'.join(
            [
                ' this is what we want to parse',
                ' behind predicate ',
                ' behind a quoted string containing percent',
            ]))
