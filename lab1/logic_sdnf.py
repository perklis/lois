# Полещук Ольга Владимировна, 421703

from __future__ import annotations
from exceptions import FormulaSyntaxError
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set


@dataclass(frozen=True)
class Lexema:
    type: str
    value: str
    pos: int


@dataclass(frozen=True)
class Node:
    pass


@dataclass(frozen=True)
class Variable(Node):
    name: str


@dataclass(frozen=True)
class Not(Node):
    child: Node


@dataclass(frozen=True)
class Connective(Node):
    op: str
    left: Node
    right: Node


@dataclass(frozen=True)
class Constant(Node):
    value: bool


def check_brackets(text: str) -> None:
    stack: List[int] = []
    for idx, ch in enumerate(text):
        if ch == "(":
            stack.append(idx)
        elif ch == ")":
            if not stack:
                raise FormulaSyntaxError("Лишняя закрывающая скобка")
            stack.pop()
    if stack:
        raise FormulaSyntaxError("Нет закрывающей скобки")


def tokenize(text: str) -> List[Lexema]:
    if not text or not text.strip():
        raise FormulaSyntaxError("Пустая формула")
    check_brackets(text)
    tokens: List[Lexema] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if text.startswith("/\\", i):
            tokens.append(Lexema("AND", "/\\", i))
            i += 2
            continue
        if text.startswith("\\/", i):
            tokens.append(Lexema("OR", "\\/", i))
            i += 2
            continue
        if text.startswith("->", i):
            tokens.append(Lexema("IMP", "->", i))
            i += 2
            continue
        if ch == "~":
            tokens.append(Lexema("EQV", "~", i))
            i += 1
            continue
        if ch == "!":
            tokens.append(Lexema("NOT", "!", i))
            i += 1
            continue
        if ch == "(":
            tokens.append(Lexema("LP", "(", i))
            i += 1
            continue
        if ch == ")":
            tokens.append(Lexema("RP", ")", i))
            i += 1
            continue
        if ch in {"0", "1"}:
            tokens.append(Lexema("CONST", ch, i))
            i += 1
            continue
        if "A" <= ch <= "Z":
            tokens.append(Lexema("VAR", ch, i))
            i += 1
            continue
        raise FormulaSyntaxError(f"Недопустимый символ '{ch}' по индексу {i + 1}")
    tokens.append(Lexema("EOF", "", len(text)))
    return tokens


def parse_formula(text: str) -> Node:
    from Parser import Parser

    return Parser(tokenize(text)).parse()

from Parser import Parser

def sort_strings(values: List[str]) -> List[str]:
    result = values[:]
    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        while j >= 0 and result[j] > current:
            result[j + 1] = result[j]
            j -= 1
        result[j + 1] = current
    return result


def extract_variables(node: Node) -> List[str]:
    names: Set[str] = set()

    def go_around_tree(current: Node) -> None:
        if isinstance(current, Variable):
            names.add(current.name)
            return
        if isinstance(current, Constant):
            return
        if isinstance(current, Not):
            go_around_tree(current.child)
            return
        if isinstance(current, Connective):
            go_around_tree(current.left)
            go_around_tree(current.right)
            return
        raise FormulaSyntaxError("Неизвестный тип узла")

    go_around_tree(node)
    return sort_strings(list(names))


def evaluate(node: Node, assignment: Dict[str, bool]) -> bool:
    if isinstance(node, Constant):
        return node.value
    if isinstance(node, Variable):
        if node.name not in assignment:
            raise FormulaSyntaxError(f"Нет значения для переменной {node.name}")
        return assignment[node.name]
    if isinstance(node, Not):
        return not evaluate(node.child, assignment)
    if isinstance(node, Connective):
        left = evaluate(node.left, assignment)
        right = evaluate(node.right, assignment)
        if node.op == "AND":
            return left and right
        if node.op == "OR":
            return left or right
        if node.op == "IMP":
            return (not left) or right
        if node.op == "EQV":
            return left == right
        raise FormulaSyntaxError(f"Неизвестная операция {node.op}")
    raise FormulaSyntaxError("Неизвестный тип узла")


def get_vars_bool_dict(
    variables: Sequence[str], values: Sequence[bool]
) -> Dict[str, bool]:
    return {variables[i]: values[i] for i in range(len(variables))}


def get_truth_table(size: int) -> List[List[bool]]:
    if size == 0:
        return [[]]
    prev = get_truth_table(size - 1)
    result: List[List[bool]] = []
    for item in prev:
        result.append(item + [False])
        result.append(item + [True])
    return result


def build_sdnf_from_tree(node: Node) -> str:
    variables = extract_variables(node)
    if not variables:
        return "1" if evaluate(node, {}) else "0"
    terms: List[str] = []
    for rows in get_truth_table(len(variables)):
        assignment = get_vars_bool_dict(variables, rows)
        if evaluate(node, assignment):
            conjuncts = [name if assignment[name] else f"!{name}" for name in variables]
            term = "/\\".join(conjuncts)
            if len(conjuncts) > 1:
                term = f"({term})"
            terms.append(term)
    if not terms:
        return "0"
    if len(terms) == 1:
        return terms[0]
    return "\\/".join(terms)


def build_sdnf(text: str) -> str:
    return build_sdnf_from_tree(parse_formula(text))
