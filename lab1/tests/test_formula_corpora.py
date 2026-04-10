import unittest
from pathlib import Path
from exceptions import FormulaSyntaxError
from logic_sdnf import Connective, Constant, Not, Variable, build_sdnf, parse_formula
# Полещук Ольга Владимировна, 421703


class FormulaCorporaTests(unittest.TestCase):
    @staticmethod
    def _resource_path(name: str) -> Path:
        return Path(__file__).resolve().parent / "resources" / name

    @staticmethod
    def _load_positive_cases(path: Path) -> list[tuple[str, int | None]]:
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        result: list[tuple[str, int | None]] = []
        if len(lines) % 2 == 0:
            pair_mode = True
            for idx in range(1, len(lines), 2):
                if not lines[idx].isdigit():
                    pair_mode = False
                    break
            if pair_mode:
                for idx in range(0, len(lines), 2):
                    result.append((lines[idx], int(lines[idx + 1])))
                return result
        for formula in lines:
            result.append((formula, None))
        return result

    @staticmethod
    def _load_negative_cases(path: Path) -> list[str]:
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    @staticmethod
    def _node_count(node: object) -> int:
        if isinstance(node, (Variable, Constant)):
            return 1
        if isinstance(node, Not):
            return 1 + FormulaCorporaTests._node_count(node.child)
        if isinstance(node, Connective):
            return (
                1
                + FormulaCorporaTests._node_count(node.left)
                + FormulaCorporaTests._node_count(node.right)
            )
        raise AssertionError("Неизвестный тип узла")

    def test_positive_formulas_from_document(self) -> None:
        cases = self._load_positive_cases(self._resource_path("positive_tests.txt"))
        for formula, expected_nodes in cases:
            with self.subTest(formula=formula):
                node = parse_formula(formula)
                if expected_nodes is not None:
                    self.assertEqual(self._node_count(node), expected_nodes)
                else:
                    self.assertGreaterEqual(self._node_count(node), 1)
                sdnf = build_sdnf(formula)
                self.assertNotEqual(sdnf, "")

    def test_negative_formulas_from_document(self) -> None:
        cases = self._load_negative_cases(self._resource_path("negative_tests.txt"))
        for formula in cases:
            with self.subTest(formula=formula):
                with self.assertRaises(FormulaSyntaxError):
                    parse_formula(formula)
