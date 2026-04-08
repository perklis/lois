import unittest
from pathlib import Path
from unittest.mock import patch
import main as main
from logic_sdnf import FormulaSyntaxError


class MainTests(unittest.TestCase):
    @staticmethod
    def _tmp_dir() -> Path:
        path = Path("tests/resources/runtime")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_read_formula_from_file_ok(self) -> None:
        file_path = self._tmp_dir() / "formula_ok.txt"
        file_path.write_text("A/\\B", encoding="utf-8")
        self.assertEqual(main.read_formula_from_file(str(file_path)), "A/\\B")

    def test_read_formula_from_file_not_found(self) -> None:
        missing = self._tmp_dir() / "missing.txt"
        if missing.exists():
            missing.unlink()
        with self.assertRaisesRegex(FormulaSyntaxError, "Файл не найден"):
            main.read_formula_from_file(str(missing))

    def test_read_formula_from_file_not_a_file(self) -> None:
        with self.assertRaisesRegex(FormulaSyntaxError, "не является файлом"):
            main.read_formula_from_file(str(self._tmp_dir()))

    def test_read_formula_from_file_empty(self) -> None:
        file_path = self._tmp_dir() / "empty.txt"
        file_path.write_text("  \n\n", encoding="utf-8")
        with self.assertRaisesRegex(FormulaSyntaxError, "Файл пуст"):
            main.read_formula_from_file(str(file_path))

    def test_read_formula_from_console_ok(self) -> None:
        with patch("builtins.input", return_value=" A "):
            self.assertEqual(main.read_formula_from_console(), "A")

    def test_read_formula_from_console_empty(self) -> None:
        with patch("builtins.input", return_value="   "):
            with self.assertRaisesRegex(FormulaSyntaxError, "не должна быть пустой"):
                main.read_formula_from_console()

    def test_process_formula(self) -> None:
        self.assertEqual(main.process_formula("A"), "A")

    def test_run_invalid_choice_then_exit(self) -> None:
        with patch("builtins.input", side_effect=["7", "0"]):
            with patch("builtins.print") as mocked_print:
                main.run()
        printed = "\n".join(" ".join(str(a) for a in call.args) for call in mocked_print.call_args_list)
        self.assertIn("Ошибка: выберите 0, 1 или 2", printed)
        self.assertIn("Выход", printed)

    def test_run_console_success(self) -> None:
        with patch("builtins.input", side_effect=["2", "A", "0"]):
            with patch("builtins.print") as mocked_print:
                main.run()
        printed = "\n".join(" ".join(str(a) for a in call.args) for call in mocked_print.call_args_list)
        self.assertIn("СДНФ: A", printed)

    def test_run_console_formula_error(self) -> None:
        with patch("builtins.input", side_effect=["2", "!A", "0"]):
            with patch("builtins.print") as mocked_print:
                main.run()
        printed = "\n".join(" ".join(str(a) for a in call.args) for call in mocked_print.call_args_list)
        self.assertIn("Ошибка:", printed)

    def test_run_file_success(self) -> None:
        file_path = self._tmp_dir() / "formula_run.txt"
        file_path.write_text("A", encoding="utf-8")
        with patch("builtins.input", side_effect=["1", str(file_path), "0"]):
            with patch("builtins.print") as mocked_print:
                main.run()
        printed = "\n".join(" ".join(str(a) for a in call.args) for call in mocked_print.call_args_list)
        self.assertIn("СДНФ: A", printed)

    def test_run_file_formula_error(self) -> None:
        with patch("builtins.input", side_effect=["1", "missing.txt", "0"]):
            with patch("builtins.print") as mocked_print:
                main.run()
        printed = "\n".join(" ".join(str(a) for a in call.args) for call in mocked_print.call_args_list)
        self.assertIn("Ошибка: Файл не найден", printed)

    def test_run_file_os_error(self) -> None:
        with patch("main.read_formula_from_file", side_effect=OSError("boom")):
            with patch("builtins.input", side_effect=["1", "anything", "0"]):
                with patch("builtins.print") as mocked_print:
                    main.run()
        printed = "\n".join(" ".join(str(a) for a in call.args) for call in mocked_print.call_args_list)
        self.assertIn("Ошибка чтения файла", printed)

    def test_run_file_unicode_error(self) -> None:
        error = UnicodeDecodeError("utf-8", b"x", 0, 1, "bad")
        with patch("main.read_formula_from_file", side_effect=error):
            with patch("builtins.input", side_effect=["1", "anything", "0"]):
                with patch("builtins.print") as mocked_print:
                    main.run()
        printed = "\n".join(" ".join(str(a) for a in call.args) for call in mocked_print.call_args_list)
        self.assertIn("Ошибка чтения файла", printed)


if __name__ == "__main__":
    unittest.main()
