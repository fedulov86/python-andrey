#!/usr/bin/env python3
"""Прогоняет каждый пример кода из уроков как отдельную программу.

Черепашка и Pygame Zero заменены заглушками: окна не открываются,
но обработчики клавиш, мыши и таймеров вызываются по одному разу.
input() отвечает по очереди из ANSWERS, а после 30 вопросов программа считается дошедшей до конца.

Запуск:  python3 check.py
"""
import contextlib
import html
import io
import json
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).parent
CODE_RE = re.compile(r'<div class="code"><pre>(.*?)</pre></div>', re.S)

# Примеры, которые ломаются нарочно (показывают ошибку): (модуль, урок, номер блока в уроке)
EXPECTED_FAIL = {
    (1, 2, 0), (1, 2, 1),   # урок про ошибки
    (1, 6, 1),              # input без int
    (2, 4, 3),              # задача «найди ошибку в отступах»
}

ANSWER_SETS = [
    ["5", "7", "3", "12", "0"],
    ["5", "да", "7", "квадрат", "выход", "3", "камень", "хватит", "", "0"],
]


class StopRun(Exception):
    pass


class Any:
    """Объект, который принимает любые атрибуты и вызовы."""
    def __init__(self, name="any"):
        self._name = name
        self.x = 0
        self.y = 0

    def __getattr__(self, item):
        if item.startswith("__"):
            raise AttributeError(item)
        return Any(item)

    def __call__(self, *a, **k):
        return Any(self._name)

    def __bool__(self):
        return False

    def __iter__(self):
        return iter([])

    def __eq__(self, other):
        return isinstance(other, Any)

    def __hash__(self):
        return 0


CALLBACKS = []


def make_turtle():
    t = types.ModuleType("turtle")

    class Turtle:
        def __init__(self):
            self._x = 0.0
            self._y = 0.0

        def __getattr__(self, item):
            return lambda *a, **k: None

        def xcor(self):
            return self._x

        def ycor(self):
            return self._y

        def distance(self, *a):
            return 100.0

        def goto(self, x, y=None):
            self._x, self._y = (x if y is not None else x[0]), (y if y is not None else x[1])

    main = Turtle()
    names = ("forward back left right circle color pensize penup pendown shape speed done write goto bgcolor "
             "setheading heading listen hideturtle showturtle clear fillcolor begin_fill end_fill dot").split()
    for n in names:
        setattr(t, n, getattr(main, n))
    t.xcor, t.ycor, t.distance = main.xcor, main.ycor, main.distance
    t.Turtle = Turtle
    t.onkey = lambda f, key: CALLBACKS.append((f, ()))
    t.onscreenclick = lambda f, *a: CALLBACKS.append((f, (10, 20)))
    t.ontimer = lambda f, ms=0: CALLBACKS.append((f, ()))
    t.__all__ = [n for n in dir(t) if not n.startswith("_")]
    return t


def make_pgz():
    m = types.ModuleType("pgzrun")
    m.go = lambda: None
    return m


class Actor:
    def __init__(self, image, pos=(0, 0)):
        self.image = image
        self.x, self.y = pos

    def draw(self):
        pass

    def colliderect(self, other):
        return True

    def collidepoint(self, pos):
        return True


class Clock:
    def schedule_interval(self, f, t):
        CALLBACKS.append((f, ()))

    def schedule(self, f, t):
        CALLBACKS.append((f, ()))


def run(code, answers):
    CALLBACKS.clear()
    asked = [0]

    def fake_input(*a):
        asked[0] += 1
        if asked[0] > 30:
            raise StopRun
        return answers[(asked[0] - 1) % len(answers)]

    sys.modules["turtle"] = make_turtle()
    sys.modules["pgzrun"] = make_pgz()
    keys = types.SimpleNamespace(SPACE="space", RETURN="return", UP="up", DOWN="down", LEFT="left", RIGHT="right", A="a", P="p")
    ns = {"__name__": "__main__", "input": fake_input, "Actor": Actor, "Rect": lambda *a: a,
          "screen": Any("screen"), "keyboard": Any("keyboard"), "keys": keys, "clock": Clock(),
          "sounds": Any("sounds"), "music": Any("music")}
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(compile(code, "x", "exec"), ns)
            if "pgzrun" in code:
                for name, args in (("update", ()), ("draw", ()), ("on_mouse_down", ((10, 20),)),
                                   ("on_key_down", (keys.SPACE,))):
                    if callable(ns.get(name)):
                        ns[name](*args)
                if callable(ns.get("draw")):
                    ns["draw"]()
            for f, args in list(CALLBACKS):
                f(*args)
        except StopRun:
            pass


def main():
    bad = 0
    total = 0
    for f in sorted(ROOT.glob("content/module*.html"), key=lambda p: int(re.search(r"\d+", p.stem).group())):
        text = f.read_text(encoding="utf-8")
        mod = json.loads(re.match(r"<!--module (.*?) -->", text).group(1))["num"]
        for m in re.finditer(r"<!--lesson (.*?) -->\n(.*?)(?=\n<!--lesson |\Z)", text, re.S):
            lesson = json.loads(m.group(1))["num"]
            for i, raw in enumerate(CODE_RE.findall(m.group(2))):
                total += 1
                code = html.unescape(re.sub(r"<[^>]+>", "", raw))
                key = (mod, lesson, i)
                err = None
                for answers in ANSWER_SETS:
                    try:
                        run(code, answers)
                        err = None
                        break
                    except BaseException as e:  # noqa: BLE001
                        err = f"{type(e).__name__}: {e}"
                if (err is None) == (key in EXPECTED_FAIL):
                    bad += 1
                    first = code.strip().splitlines()[0][:50]
                    what = err or "должен был упасть, но отработал"
                    print(f"модуль {mod}, урок {lesson}, блок {i}: {first!r} → {what}")
    print(f"Проверено блоков: {total}, проблем: {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
