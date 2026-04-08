import unittest
from exceptions import FormulaSyntaxError
from logic_sdnf import (
    Connective,
    Constant,
    Node,
    Not,
    Parser,
    Lexema,
    Variable,
    get_vars_bool_dict,
    build_sdnf,
    build_sdnf_from_tree,
    check_brackets,
    evaluate,
    extract_variables,
    get_truth_table,
    parse_formula,
    tokenize,
)



class LogicSdnfTests(unittest.TestCase):
    def test_check_parentheses_balance_ok(self) -> None:
        check_brackets("(!(A\\/B)/\\C)")

    def test_check_parentheses_balance_extra_closing(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Лишняя закрывающая скобка"):
            check_brackets("A)")

    def test_check_parentheses_balance_missing_closing(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Нет закрывающей скобки"):
            check_brackets("(A")

    def test_tokenize_empty(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Пустая формула"):
            tokenize("   ")

    def test_tokenize_invalid_symbol(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Недопустимый символ"):
            tokenize("A#a")

    def test_tokenize_missing_closing_by_balance_check(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Нет закрывающей скобки"):
            tokenize("(A")

    def test_tokenize_full_operator_set(self) -> None:
        tokens = tokenize("!(A/\\B)\\/C->D~E")
        kinds = [token.type for token in tokens]
        self.assertEqual(
            kinds,
            [
                "NOT",
                "LP",
                "VAR",
                "AND",
                "VAR",
                "RP",
                "OR",
                "VAR",
                "IMP",
                "VAR",
                "EQV",
                "VAR",
                "EOF",
            ],
        )

    def test_tokenize_ignores_whitespace(self) -> None:
        tokens = tokenize("  A   /\\   B  ")
        kinds = [token.type for token in tokens]
        self.assertEqual(kinds, ["VAR", "AND", "VAR", "EOF"])

    def test_tokenize_constants(self) -> None:
        tokens = tokenize("1/\\0")
        kinds = [token.type for token in tokens]
        self.assertEqual(kinds, ["CONST", "AND", "CONST", "EOF"])

    def test_parser_consume_mismatch(self) -> None:
        parser = Parser(tokenize("A"))
        with self.assertRaisesRegex(FormulaSyntaxError, "Ожидалась логическая связка"):
            parser.consume("OR")

    def test_parser_consume_expected_rp_but_eof(self) -> None:
        parser = Parser([Lexema("EOF", "", 0)])
        with self.assertRaisesRegex(FormulaSyntaxError, "Ожидалась закрывающая скобка"):
            parser.consume("RP")

    def test_parser_consume_expected_rp_but_variable(self) -> None:
        parser = Parser([Lexema("VAR", "A", 0)])
        with self.assertRaisesRegex(FormulaSyntaxError, "Ожидалась логическая связка"):
            parser.consume("RP")

    def test_parser_consume_generic_mismatch(self) -> None:
        parser = Parser(tokenize("A"))
        with self.assertRaisesRegex(FormulaSyntaxError, "Синтаксическая ошибка"):
            parser.consume("LP")

    def test_parse_formula_precedence_and_or(self) -> None:
        node = parse_formula("((A\\/B)/\\C)")
        self.assertIsInstance(node, Connective)
        self.assertEqual(node.op, "AND")
        self.assertIsInstance(node.left, Connective)
        self.assertEqual(node.left.op, "OR")
        self.assertIsInstance(node.right, Variable)
        self.assertEqual(node.right.name, "C")

    def test_parse_formula_implication_right_associative(self) -> None:
        node = parse_formula("(A->(B->C))")
        result = evaluate(node, {"A": False, "B": True, "C": False})
        self.assertTrue(result)

    def test_parse_formula_equivalence_chain(self) -> None:
        node = parse_formula("((A~B)~C)")
        result = evaluate(node, {"A": True, "B": True, "C": False})
        self.assertFalse(result)

    def test_parse_formula_requires_outer_parentheses_for_binary(self) -> None:
        with self.assertRaisesRegex(
            FormulaSyntaxError, "со связкой должна быть обрамлена внешними скобками"
        ):
            parse_formula("A~A")

    def test_parse_formula_parenthesized_variable(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Ожидалась логическая связка"):
            parse_formula("(A)")

    def test_parse_formula_constant(self) -> None:
        node = parse_formula("1")
        self.assertIsInstance(node, Constant)
        self.assertTrue(evaluate(node, {}))

    def test_parse_formula_unexpected_second_variable(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Ожидалась логическая связка"):
            parse_formula("AB")

    def test_parse_formula_missing_operator_between_groups(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Ожидалась логическая связка"):
            parse_formula("(((A/\\A)(!B)))")

    def test_parse_formula_double_negation_without_brackets_invalid(self) -> None:
        with self.assertRaisesRegex(
            FormulaSyntaxError, "отрицание должно быть обрамлено скобками"
        ):
            parse_formula("((!!A))")

    def test_parse_formula_double_negation_with_brackets_valid(self) -> None:
        node = parse_formula("(!(!A))")
        self.assertIsInstance(node, Not)

    def test_parse_formula_unary_without_outer_brackets_invalid(self) -> None:
        with self.assertRaisesRegex(
            FormulaSyntaxError, "отрицание должно быть обрамлено скобками"
        ):
            parse_formula("!A")

    def test_parse_formula_chain_without_binary_brackets_invalid(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Ожидалась закрывающая скобка"):
            parse_formula("((A~A~A))")

    def test_parse_formula_extra_right_parenthesis_message(self) -> None:
        parser = Parser(
            [Lexema("VAR", "A", 0), Lexema("RP", ")", 1), Lexema("EOF", "", 2)]
        )
        with self.assertRaisesRegex(FormulaSyntaxError, "Лишняя закрывающая скобка"):
            parser.parse()

    def test_parse_formula_generic_tail_message(self) -> None:
        parser = Parser(
            [Lexema("VAR", "A", 0), Lexema("BAD", "?", 1), Lexema("EOF", "", 2)]
        )
        with self.assertRaisesRegex(FormulaSyntaxError, "Синтаксическая ошибка"):
            parser.parse()

    def test_parse_formula_missing_unary_operand(self) -> None:
        with self.assertRaisesRegex(
            FormulaSyntaxError, "отрицание должно быть обрамлено скобками"
        ):
            parse_formula("!")

    def test_parse_formula_empty_parentheses(self) -> None:
        with self.assertRaisesRegex(
            FormulaSyntaxError, "Ожидалась переменная|Ожидалась логическая связка"
        ):
            parse_formula("()")

    def test_extract_variables_sorted_unique(self) -> None:
        node = parse_formula("((B/\\A)\\/B)")
        self.assertEqual(extract_variables(node), ["A", "B"])

    def test_extract_variables_ignores_constants(self) -> None:
        node = parse_formula("(A/\\1)")
        self.assertEqual(extract_variables(node), ["A"])

    def test_extract_variables_unknown_node(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Неизвестный тип узла"):
            extract_variables(Node())

    def test_evaluate_var_missing_assignment(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Нет значения для переменной"):
            evaluate(Variable("A"), {})

    def test_evaluate_unknown_operation(self) -> None:
        bad = Connective("X", Variable("A"), Variable("B"))
        with self.assertRaisesRegex(FormulaSyntaxError, "Неизвестная операция"):
            evaluate(bad, {"A": True, "B": False})

    def test_evaluate_unknown_node_type(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "Неизвестный тип узла"):
            evaluate(Node(), {})

    def test_evaluate_all_binary_operations(self) -> None:
        and_node = Connective("AND", Variable("A"), Variable("B"))
        or_node = Connective("OR", Variable("A"), Variable("B"))
        imp_node = Connective("IMP", Variable("A"), Variable("B"))
        eqv_node = Connective("EQV", Variable("A"), Variable("B"))
        assignment = {"A": True, "B": False}
        self.assertFalse(evaluate(and_node, assignment))
        self.assertTrue(evaluate(or_node, assignment))
        self.assertFalse(evaluate(imp_node, assignment))
        self.assertFalse(evaluate(eqv_node, assignment))
        self.assertTrue(evaluate(Not(Variable("B")), assignment))

    def test_evaluate_constant_node(self) -> None:
        self.assertFalse(evaluate(Constant(False), {}))
        self.assertTrue(evaluate(Constant(True), {}))

    def test_evaluate_eqv_true_case(self) -> None:
        node = Connective("EQV", Variable("A"), Variable("B"))
        self.assertTrue(evaluate(node, {"A": False, "B": False}))

    def test_assignment_from_tuple(self) -> None:
        self.assertEqual(
            get_vars_bool_dict(["A", "B"], [True, False]), {"A": True, "B": False}
        )

    def test_generate_boolean_tuples(self) -> None:
        self.assertEqual(get_truth_table(0), [[]])
        self.assertEqual(get_truth_table(1), [[False], [True]])

    def test_build_sdnf_single_variable(self) -> None:
        self.assertEqual(build_sdnf("A"), "A")

    def test_build_sdnf_single_variable_negated(self) -> None:
        self.assertEqual(build_sdnf("(!A)"), "!A")

    def test_build_sdnf_conjunction(self) -> None:
        self.assertEqual(build_sdnf("(A/\\B)"), "(A/\\B)")

    def test_build_sdnf_disjunction(self) -> None:
        self.assertEqual(build_sdnf("(A\\/B)"), "(!A/\\B)\\/(A/\\!B)\\/(A/\\B)")

    def test_build_sdnf_contradiction(self) -> None:
        self.assertEqual(build_sdnf("(A/\\(!A))"), "0")

    def test_build_sdnf_tautology(self) -> None:
        self.assertEqual(build_sdnf("(A\\/(!A))"), "!A\\/A")

    def test_build_sdnf_from_ast_direct(self) -> None:
        node = Connective("OR", Variable("A"), Variable("B"))
        self.assertEqual(build_sdnf_from_tree(node), "(!A/\\B)\\/(A/\\!B)\\/(A/\\B)")

    def test_build_sdnf_true_constant(self) -> None:
        self.assertEqual(build_sdnf("1"), "1")

    def test_build_sdnf_false_constant(self) -> None:
        self.assertEqual(build_sdnf("0"), "0")

    def test_build_sdnf_expression_with_constant(self) -> None:
        self.assertEqual(build_sdnf("(A/\\1)"), "A")
        self.assertEqual(build_sdnf("(A\\/0)"), "A")


if __name__ == "__main__":
    unittest.main()
