#!/usr/bin/env python3
"""Собирает сайт курса в папку site/.

Каждый модуль — один файл content/moduleN.html:
    <!--module {"num": 2, "title": ..., "weeks": ..., "topics": ..., "project": ..., "lead": ...} -->
    <!--lesson {"num": 1, "title": ..., "sub": ..., "done_label": ...} -->
    ...html урока...
    <!--lesson {...} -->
    ...

Запуск:  python3 build.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
CONTENT = ROOT / "content"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700'
         '&family=Onest:wght@400;500;700&family=JetBrains+Mono:ital,wght@0,400;0,600;1,400&display=swap">')

NAV = [("index.html", "главная"), ("karta.html", "модули"),
       ("scratch.html", "scratch→python"), ("dlya-papy.html", "для_папы")]

# ---------- подсветка Python в стиле Twilight ----------
KEYWORDS = set("False None True and as break class continue def elif else for from if import in is not or pass "
               "return while with lambda try except finally raise global yield".split())
BUILTINS = set("print input int str len float range list dict abs round type min max sum bool "
               "forward back left right circle color pensize penup pendown shape speed done write goto bgcolor "
               "setheading heading onkey listen ontimer onscreenclick hideturtle showturtle Turtle xcor ycor "
               "distance clear fillcolor begin_fill end_fill dot".split())
TOK = re.compile(r'(?P<c>#[^\n]*)'
                 r'|(?P<s>[fF]?(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:[^"\\\n]|\\.)*"?|\'(?:[^\'\\\n]|\\.)*\'?))'
                 r'|(?P<n>\b\d+(?:\.\d+)?\b)'
                 r'|(?P<id>[A-Za-z_]\w*)'
                 r'|(?P<o>.)', re.S)


def span(cls, text):
    return f'<span class="{cls}">{html.escape(text, quote=False)}</span>'


def fstring(tok):
    out, last = [], 0
    for m in re.finditer(r'\{[^{}]*\}', tok):
        out.append(span("t-s", tok[last:m.start()]))
        out.append(span("t-i", m.group(0)))
        last = m.end()
    out.append(span("t-s", tok[last:]))
    return "".join(out)


def highlight(code):
    out, prev = [], ""
    for m in TOK.finditer(code):
        kind, tok = m.lastgroup, m.group(0)
        if kind == "c":
            out.append(span("t-c", tok))
        elif kind == "s":
            out.append(fstring(tok) if tok[0] in "fF" else span("t-s", tok))
        elif kind == "n":
            out.append(span("t-n", tok))
        elif kind == "id":
            if tok in KEYWORDS:
                out.append(span("t-k", tok))
            elif prev == ".":
                out.append(span("t-m", tok))
            elif tok in BUILTINS:
                out.append(span("t-f", tok))
            else:
                out.append(html.escape(tok, quote=False))
        else:
            out.append(html.escape(tok, quote=False))
        if not tok.isspace():
            prev = tok
    return "".join(out)


def code_text(raw_html):
    return html.unescape(re.sub(r"<[^>]+>", "", raw_html)).strip("\n")


def code_block(raw_html, fname):
    code = code_text(raw_html)
    lines = code.count("\n") + 1
    gut = "\n".join(str(i) for i in range(1, lines + 1))
    return (f'<div class="code"><div class="code-bar"><span>{fname}</span>'
            f'<button class="copy" type="button">Копировать</button></div>'
            f'<pre><span class="gut" aria-hidden="true">{gut}</span><code>{highlight(code)}</code></pre></div>')


CODE_RE = re.compile(r'<div class="code"><pre>(.*?)</pre></div>', re.S)


def convert_code(body, fname):
    return CODE_RE.sub(lambda m: code_block(m.group(1), fname), body)


# ---------- загрузка модулей ----------
def load_modules():
    modules = []
    for f in sorted(CONTENT.glob("module*.html"), key=lambda p: int(re.search(r"\d+", p.stem).group())):
        text = f.read_text(encoding="utf-8")
        head = re.match(r"<!--module (.*?) -->", text)
        mod = json.loads(head.group(1))
        mod["lessons"] = []
        for m in re.finditer(r"<!--lesson (.*?) -->\n(.*?)(?=\n<!--lesson |\Z)", text, re.S):
            L = json.loads(m.group(1))
            L["body"] = m.group(2).strip()
            L["module"] = mod["num"]
            L["id"] = f'm{mod["num"]}-{L["num"]}'
            L["url"] = f'lessons/m{mod["num"]}-{L["num"]}.html'
            mod["lessons"].append(L)
        modules.append(mod)
    return modules


# ---------- шаблон страницы ----------
CUR = ' aria-current="page"'


def page(title, main, root="", active=None, lesson_id=None):
    nav = "".join(
        f'<a href="{root}{href}"{CUR if href == active else ""}>{label}</a>'
        for href, label in NAV)
    data = f' data-root="{root}"' + (f' data-lesson="{lesson_id}"' if lesson_id else "")
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
{FONTS}
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body{data}>
<header class="top"><div class="top-in"><a class="logo" href="{root}index.html">python_для_андрея</a><nav>{nav}</nav></div></header>
<main class="wrap">
{main}
</main>
<script src="{root}assets/lessons.js"></script>
<script src="{root}assets/app.js"></script>
</body>
</html>
"""


def lesson_page(L, prev, nxt, mod, next_mod):
    body = convert_code(L["body"], f'm{mod["num"]}_urok{L["num"]}.py')
    last = mod["lessons"][-1]["num"]
    if prev:
        prev_html = f'<a href="../{prev["url"]}"><small>← урок {prev["num"]}</small><span class="pt">{prev["title"]}</span></a>'
    else:
        prev_html = f'<a href="../module{mod["num"]}.html"><small>← назад</small><span class="pt">Модуль {mod["num"]}</span></a>'
    if nxt:
        next_html = f'<a class="nx" href="../{nxt["url"]}"><small>урок {nxt["num"]} →</small><span class="pt">{nxt["title"]}</span></a>'
    elif next_mod:
        next_html = (f'<a class="nx" href="../module{next_mod["num"]}.html"><small>модуль {mod["num"]} закончен →</small>'
                     f'<span class="pt">Модуль {next_mod["num"]}. {next_mod["title"]}</span></a>')
    else:
        next_html = '<a class="nx" href="../karta.html"><small>курс закончен →</small><span class="pt">Все модули</span></a>'
    main = f"""<div class="head">
  <span class="eyebrow">модуль {mod["num"]} · урок {L["num"]} из {last}</span>
  <h1>{L["title"]}</h1>
  <p class="lead">{L["sub"]}</p>
</div>
<article class="body">
{body}
</article>
<div class="finish">
  <button class="btn" id="doneBtn" type="button" data-label="{html.escape(L["done_label"])}">{html.escape(L["done_label"])}</button>
  <nav class="pager" aria-label="Соседние уроки">{prev_html}{next_html}</nav>
</div>"""
    return page(f'Урок {L["num"]}. {L["title"]}', main, root="../", active="karta.html", lesson_id=L["id"])


def module_page(mod):
    items = "\n".join(
        f'  <li><a href="{L["url"]}" data-lesson-link="{L["id"]}"><span class="ln">{L["num"]}</span>'
        f'<span class="lt">{L["title"]}<small>{L["sub"]}</small></span><span class="st">не пройден</span></a></li>'
        for L in mod["lessons"])
    main = f"""<div class="head">
  <span class="eyebrow">модуль {mod["num"]} · {mod["weeks"]}</span>
  <h1>{mod["title"]}</h1>
  <p class="lead">{mod["lead"]}</p>
</div>
<div class="continue">
  <div class="prog-top"><span>Пройдено</span><span class="num" data-mod-progress="{mod["num"]}">0 из {len(mod["lessons"])}</span></div>
  <div class="bar"><i data-mod-bar="{mod["num"]}"></i></div>
</div>
<ol class="llist">
{items}
</ol>
<footer>Отметки хранятся в этом браузере. На другом компьютере их не будет.</footer>"""
    return page(f'Модуль {mod["num"]}. {mod["title"]}', main, active="karta.html")


def karta_page(modules):
    items = []
    for mod in modules:
        n = mod["num"]
        items.append(
            f'  <li data-mod="{n}"><span class="dot">{n}</span><div class="mod">'
            f'<div class="mod-head"><h3><a href="module{n}.html">{mod["title"]}</a></h3><span class="weeks">{mod["weeks"]}</span>'
            f'<span class="chip" data-mod-chip="{n}" hidden>ты здесь</span></div>'
            f'<p>{mod["topics"]}</p><p class="proj">Проект: {mod["project"]}</p>'
            f'<p class="weeks"><span data-mod-progress="{n}">0 из {len(mod["lessons"])}</span> уроков</p></div></li>')
    main = f"""<div class="head">
  <span class="eyebrow">маршрут · ~18 недель</span>
  <h1>Модули курса</h1>
  <p class="lead">Семь модулей, в конце каждого свой проект. Иди по порядку: каждый модуль опирается на предыдущий.</p>
</div>
<ol class="route">
{chr(10).join(items)}
</ol>"""
    return page("Модули курса", main, active="karta.html")


# ---------- простые страницы ----------
INDEX = """<div class="head">
  <span class="eyebrow">курс программирования · python 3 · windows</span>
  <h1>Python для <span class="hl">Андрея</span></h1>
  <p class="lead">Ты уже делал игры в Scratch. Здесь то же самое, только команды пишутся текстом. Через четыре месяца у тебя будет своя игра на Python.</p>
</div>
<section class="card continue">
  <div class="prog-top"><span id="curModule">Модуль 1 · Старт</span><span class="num" id="progNum"></span></div>
  <div class="bar"><i id="progBar"></i></div>
  <p class="next-title" id="nextTitle">Урок 0. Устанавливаем Thonny</p>
  <div><a class="btn" id="continueLink" href="lessons/m1-0.html">Начать с урока 0 →</a></div>
</section>
<section class="head">
  <span class="eyebrow">как заниматься · час в день, 5 дней в неделю</span>
  <div class="day">
    <div><b>10 мин</b>Повтори прошлый урок: открой свой код и запусти его.</div>
    <div><b>35 мин</b>Новый урок: прочитай, перепечатай пример, реши задачи.</div>
    <div><b>15 мин</b>Свободно: поменяй что-нибудь в коде и посмотри, что будет.</div>
  </div>
</section>
<p class="muted">Все модули по неделям — на странице <a href="karta.html">модули</a>. Если что-то из Scratch забыл, загляни в <a href="scratch.html">шпаргалку</a>.</p>"""

SCRATCH = """<div class="head">
  <span class="eyebrow">шпаргалка</span>
  <h1>Из Scratch в Python</h1>
  <p class="lead">Почти всё, что ты знаешь по Scratch, в Python тоже есть. Просто это пишется словами.</p>
</div>
<div class="tbl"><table>
  <thead><tr><th>блок в scratch</th><th>в python</th><th>где учим</th></tr></thead>
  <tbody>
    <tr><td><span class="blk b-ev">когда щёлкнут по флажку</span></td><td>Кнопка ▶ или F5 в Thonny. Программа выполняется сверху вниз</td><td>м1 · урок 0</td></tr>
    <tr><td><span class="blk b-look">сказать Привет!</span></td><td><code>print("Привет!")</code></td><td>м1 · урок 1</td></tr>
    <tr><td><span class="blk b-var">задать счёт значение 0</span></td><td><code>score = 0</code></td><td>м1 · урок 3</td></tr>
    <tr><td><span class="blk b-var">изменить счёт на 1</span></td><td><code>score += 1</code></td><td>м1 · урок 4</td></tr>
    <tr><td><span class="blk b-op">объединить</span></td><td><code>"при" + "вет"</code></td><td>м1 · урок 5</td></tr>
    <tr><td><span class="blk b-sense">спросить и ждать</span></td><td><code>answer = input("Вопрос? ")</code></td><td>м1 · урок 6</td></tr>
    <tr><td><span class="blk b-look">идти 10 шагов</span> <span class="blk b-look">повернуть на 90</span></td><td><code>forward(10)</code>, <code>left(90)</code></td><td>м1 · урок 8</td></tr>
    <tr><td><span class="blk b-ctl">если … то … иначе</span></td><td><code>if …:</code> / <code>else:</code></td><td>м2</td></tr>
    <tr><td><span class="blk b-ctl">повторить 10 раз</span></td><td><code>for i in range(10):</code></td><td>м3</td></tr>
    <tr><td><span class="blk b-ctl">повторять пока не</span></td><td><code>while …:</code></td><td>м3</td></tr>
    <tr><td><span class="blk b-op">выдать случайное от 1 до 10</span></td><td><code>random.randint(1, 10)</code></td><td>м3</td></tr>
    <tr><td><span class="blk b-look">свои блоки</span></td><td><code>def имя():</code></td><td>м4</td></tr>
    <tr><td><span class="blk b-ev">когда клавиша нажата</span></td><td><code>onkey(функция, "Left")</code></td><td>м4</td></tr>
    <tr><td><span class="blk b-var">список</span></td><td><code>items = ["меч", "щит"]</code></td><td>м5</td></tr>
    <tr><td><span class="blk b-sense">касается спрайта?</span></td><td><code>hero.colliderect(coin)</code></td><td>м6</td></tr>
  </tbody>
</table></div>"""

PARENT = """<div class="head">
  <span class="eyebrow">для папы</span>
  <h1>Как помогать, не делая за него</h1>
</div>
<div class="rules">
  <div class="card"><h3>Правило 15 минут</h3><p>Застрял — сначала 15 минут пробует сам: перечитывает ошибку, подсказку, урок. Потом можно спросить вас или ИИ.</p></div>
  <div class="card"><h3>Пусть объясняет</h3><p>Раз в неделю Андрей показывает, что сделал, и рассказывает, как работает код. Может объяснить — значит понял.</p></div>
  <div class="card"><h3>Вопросы вместо ответов</h3><p>«Что написано в ошибке?», «Что должно было выйти?», «Какая строчка выполнилась последней?»</p></div>
  <div class="card"><h3>ИИ как учитель</h3><p>Можно: «объясни ошибку», «что делает эта строчка». Нельзя: «напиши программу». Хорошая фраза: «не давай код, дай подсказку».</p></div>
  <div class="card"><h3>Хвалите за проекты</h3><p>Отмечайте законченные проекты, а не скорость. Пропустить день нормально. Бросить проект на середине — нет.</p></div>
  <div class="card"><h3>Если стало скучно</h3><p>Можно сразу перейти к проекту модуля или поменять тему задач на то, что ему интересно.</p></div>
</div>
<p class="muted">Хорошие знаки: он сам меняет код «а что будет, если…», придумывает свои задачи, рассказывает о программах без просьбы.</p>"""


def main():
    modules = load_modules()
    (SITE / "lessons").mkdir(parents=True, exist_ok=True)
    for old in (SITE / "lessons").glob("*.html"):
        old.unlink()
    for old in SITE.glob("module*.html"):
        old.unlink()
    pages = {
        "index.html": page("Python для Андрея", INDEX, active="index.html"),
        "karta.html": karta_page(modules),
        "scratch.html": page("Из Scratch в Python", SCRATCH, active="scratch.html"),
        "dlya-papy.html": page("Для папы", PARENT, active="dlya-papy.html"),
    }
    flat = []
    for i, mod in enumerate(modules):
        pages[f'module{mod["num"]}.html'] = module_page(mod)
        next_mod = modules[i + 1] if i + 1 < len(modules) else None
        ls = mod["lessons"]
        for j, L in enumerate(ls):
            prev = ls[j - 1] if j > 0 else None
            nxt = ls[j + 1] if j + 1 < len(ls) else None
            pages[L["url"]] = lesson_page(L, prev, nxt, mod, next_mod)
            flat.append({"id": L["id"], "m": mod["num"], "n": L["num"], "t": L["title"], "u": L["url"]})
    mods = [{"m": m["num"], "t": m["title"], "count": len(m["lessons"])} for m in modules]
    (SITE / "assets" / "lessons.js").write_text(
        "window.LESSONS = " + json.dumps(flat, ensure_ascii=False) + ";\n"
        "window.MODULES = " + json.dumps(mods, ensure_ascii=False) + ";\n", encoding="utf-8")
    for path, text in pages.items():
        (SITE / path).write_text(text, encoding="utf-8")
    print(f"Модулей: {len(modules)}, уроков: {len(flat)}, страниц: {len(pages)}")


if __name__ == "__main__":
    main()
