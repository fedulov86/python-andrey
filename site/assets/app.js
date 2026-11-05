(function () {
  var KEY = 'andrey-python-progress';
  var LESSONS = window.LESSONS || [];
  var MODULES = window.MODULES || [];
  var root = document.body.getAttribute('data-root') || '';
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { state = {}; }

  // старые отметки модуля 1 (l0, l1, ...) переносим в новый формат (m1-0, m1-1, ...)
  Object.keys(state).forEach(function (k) {
    var m = /^l(\d+)$/.exec(k);
    if (m) { if (state[k]) state['m1-' + m[1]] = true; delete state[k]; }
  });
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
  save();

  function modTitle(m) { var x = MODULES.find(function (y) { return y.m === m; }); return x ? x.t : ''; }
  function doneIn(m) { return LESSONS.filter(function (l) { return l.m === m && state[l.id]; }).length; }
  function countIn(m) { return LESSONS.filter(function (l) { return l.m === m; }).length; }

  function render() {
    var next = LESSONS.find(function (l) { return !state[l.id]; });
    var curMod = next ? next.m : (MODULES.length ? MODULES[MODULES.length - 1].m : 1);

    // главная
    var numEl = document.getElementById('progNum');
    if (numEl) numEl.textContent = doneIn(curMod) + ' из ' + countIn(curMod);
    var bar = document.getElementById('progBar');
    if (bar) bar.style.width = (doneIn(curMod) / Math.max(1, countIn(curMod)) * 100) + '%';
    var cm = document.getElementById('curModule');
    if (cm) cm.textContent = 'Модуль ' + curMod + ' · ' + modTitle(curMod);
    var cont = document.getElementById('continueLink');
    var nt = document.getElementById('nextTitle');
    if (cont) {
      if (next) {
        cont.href = root + next.u;
        var any = LESSONS.some(function (l) { return state[l.id]; });
        cont.textContent = any ? 'Продолжить: урок ' + next.n + ' →' : 'Начать с урока 0 →';
        if (nt) nt.textContent = 'Урок ' + next.n + '. ' + next.t;
      } else {
        cont.href = root + 'karta.html';
        cont.textContent = 'Курс пройден! Открыть модули';
        if (nt) nt.textContent = 'Ты прошёл весь курс';
      }
    }

    // прогресс по модулям
    document.querySelectorAll('[data-mod-progress]').forEach(function (el) {
      var m = +el.getAttribute('data-mod-progress');
      el.textContent = doneIn(m) + ' из ' + countIn(m);
    });
    document.querySelectorAll('[data-mod-bar]').forEach(function (el) {
      var m = +el.getAttribute('data-mod-bar');
      el.style.width = (doneIn(m) / Math.max(1, countIn(m)) * 100) + '%';
    });
    document.querySelectorAll('[data-mod]').forEach(function (el) {
      var m = +el.getAttribute('data-mod');
      el.classList.toggle('now', m === curMod);
      var chip = el.querySelector('[data-mod-chip]');
      if (chip) chip.hidden = m !== curMod;
    });

    // списки уроков
    document.querySelectorAll('[data-lesson-link]').forEach(function (a) {
      var id = a.getAttribute('data-lesson-link');
      var isNext = !!next && next.id === id;
      a.classList.toggle('is-done', !!state[id]);
      a.classList.toggle('is-next', isNext);
      var st = a.querySelector('.st');
      if (st) st.textContent = state[id] ? 'пройден' : (isNext ? 'следующий' : 'не пройден');
    });

    // кнопка на странице урока
    var btn = document.getElementById('doneBtn');
    if (btn) {
      var lid = document.body.getAttribute('data-lesson');
      var label = btn.getAttribute('data-label');
      btn.classList.toggle('done', !!state[lid]);
      btn.textContent = state[lid] ? '✓ Пройден. Нажми, чтобы снять отметку' : '☐ ' + label;
    }
  }

  var btn = document.getElementById('doneBtn');
  if (btn) btn.addEventListener('click', function () {
    var lid = document.body.getAttribute('data-lesson');
    state[lid] = !state[lid];
    save(); render();
  });

  document.querySelectorAll('.copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var code = b.closest('.code').querySelector('pre code');
      function ok() { b.textContent = 'Скопировано'; setTimeout(function () { b.textContent = 'Копировать'; }, 1500); }
      function fallback() {
        var r = document.createRange(); r.selectNodeContents(code);
        var s = getSelection(); s.removeAllRanges(); s.addRange(r);
        b.textContent = 'Нажми Ctrl+C';
      }
      try { navigator.clipboard.writeText(code.textContent).then(ok, fallback); } catch (e) { fallback(); }
    });
  });

  render();
})();
