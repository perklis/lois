from __future__ import annotations
from pathlib import Path
from logic_sdnf import FormulaSyntaxError, build_sdnf
# Полещук Ольга Владимировна, 421703

def read_formula_from_file(path_text: str) -> str:
    path = Path(path_text).expanduser()
    if not path.exists():
        raise FormulaSyntaxError("Файл не найден")
    if not path.is_file():
        raise FormulaSyntaxError("Указанный путь не является файлом")
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise FormulaSyntaxError("Файл пуст")
    return content

def read_formula_from_console() -> str:
    text = input("Введите формулу: ").strip()
    if not text:
        raise FormulaSyntaxError("Формула не должна быть пустой")
    return text

def process_formula(formula: str) -> str:
    return build_sdnf(formula)

def run() -> None:
    while True:
        print("\nМеню:")
        print("1. Загрузить формулу из файла")
        print("2. Ввести формулу в консоль")
        print("0. Выход")
        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            return

        if choice == "1":
            path_text = input("Введите путь к файлу: ").strip()
            try:
                formula = read_formula_from_file(path_text)
                sdnf = process_formula(formula)
                print(f"СДНФ: {sdnf}")
            except (OSError, UnicodeDecodeError):
                print("Ошибка чтения файла")
            except FormulaSyntaxError as error:
                print(f"Ошибка: {error}")
            continue

        if choice == "2":
            try:
                formula = read_formula_from_console()
                sdnf = process_formula(formula)
                print(f"СДНФ: {sdnf}")
            except FormulaSyntaxError as error:
                print(f"Ошибка: {error}")
            continue
        print("Ошибка: выберите 0, 1 или 2")

if __name__ == "__main__":
    run()
