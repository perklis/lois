from __future__ import annotations
from exceptions import FormulaSyntaxError
from typing import Sequence
from logic_sdnf import Lexema, Node, Variable, Not, Connective, Constant

class Parser:
    def __init__(self, tokens: Sequence[Lexema]):
        self.tokens = tokens
        self.index = 0

    def current(self) -> Lexema:
        return self.tokens[self.index]

    def consume(self, type: str) -> Lexema:
        token = self.current()
        if token.type != type:
            if type == "RP":
                if token.type in {"LP", "VAR", "NOT", "CONST"}:
                    raise FormulaSyntaxError(
                        f"Ожидалась логическая связка в позиции {token.pos + 1}"
                    )
                raise FormulaSyntaxError(
                    f"Ожидалась закрывающая скобка в позиции {token.pos + 1}"
                )
            if type in {"AND", "OR", "IMP", "EQV"}:
                raise FormulaSyntaxError(
                    f"Ожидалась логическая связка в позиции {token.pos + 1}"
                )
            raise FormulaSyntaxError(f"Синтаксическая ошибка в позиции {token.pos + 1}")
        self.index += 1
        return token

    def parse(self) -> Node:
        node = self.parse_expression()
        if self.current().type != "EOF":
            token = self.current()
            if token.type in {"AND", "OR", "IMP", "EQV"}:
                raise FormulaSyntaxError(
                    "Ошибка ввода формулы: формула со связкой должна быть обрамлена внешними скобками"
                )
            if token.type in {"LP", "VAR", "NOT", "CONST"}:
                raise FormulaSyntaxError(
                    f"Ожидалась логическая связка в позиции {token.pos + 1}"
                )
            if token.type == "RP":
                raise FormulaSyntaxError(
                    f"Лишняя закрывающая скобка в позиции {token.pos + 1}"
                )
            raise FormulaSyntaxError(f"Синтаксическая ошибка в позиции {token.pos + 1}")
        return node

    def parse_expression(self) -> Node:
        token = self.current()
        if token.type == "VAR":
            return Variable(self.consume("VAR").value)
        if token.type == "CONST":
            return Constant(self.consume("CONST").value == "1")
        if token.type == "NOT":
            raise FormulaSyntaxError(
                f"отрицание должно быть обрамлено скобками в позиции {token.pos + 1}"
            )
        if token.type == "LP":
            self.consume("LP")
            if self.current().type == "NOT":
                self.consume("NOT")
                node = Not(self.parse_expression())
                self.consume("RP")
                return node
            left = self.parse_expression()
            if self.current().type not in {"AND", "OR", "IMP", "EQV"}:
                token = self.current()
                if token.type == "RP":
                    raise FormulaSyntaxError(
                        f"Ожидалась логическая связка в позиции {token.pos + 1}"
                    )
                raise FormulaSyntaxError(
                    f"Ожидалась логическая связка в позиции {token.pos + 1}"
                )
            op = self.current().type
            self.consume(op)
            right = self.parse_expression()
            node = Connective(op, left, right)
            self.consume("RP")
            return node
        raise FormulaSyntaxError(
            f"Ожидалась переменная, константа, отрицание или '(' в позиции {token.pos + 1}"
        )
