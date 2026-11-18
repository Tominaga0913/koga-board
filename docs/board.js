// コガバス発車標(GitHub Pages 版)。build_pages.py が作った時刻表JSONを読み、
// ブラウザの中で次の発車を計算して表示する。設定は各ページの window.BOARD。
(function () {
  "use strict";
  const C = window.BOARD;
  const REFRESH_MS = 15000;          // 残り時間を計算し直す間隔
  const board = document.getElementById("board");
  let data = null;

  // ---------- 日本時間 ----------
  // パソコンの時計(世界共通の時刻)に9時間足して、日本の日付・時刻を出す
  const jstNow = () => {
    const t = new Date(Date.now() + 9 * 3600 * 1000);
    return {
      date: t.toISOString().slice(0, 10),                       // "2026-11-18"
      sec: t.getUTCHours() * 3600 + t.getUTCMinutes() * 60 + t.getUTCSeconds(),
      weekday: t.getUTCDay(),                                   // 0=日 … 6=土
      hhmm: String(t.getUTCHours()).padStart(2, "0") + ":" + String(t.getUTCMinutes()).padStart(2, "0"),
    };
  };
  const addDays = (iso, n) => {
    const t = new Date(iso + "T00:00:00Z");
    t.setUTCDate(t.getUTCDate() + n);
    return t.toISOString().slice(0, 10);
  };
  const fmt = (sec) => {
    const m = Math.floor(sec / 60);
    return String(Math.floor(m / 60) % 24).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0");
  };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const leftText = (m) => {
    if (m <= 0) return "まもなく発車";
    const h = Math.floor(m / 60), mm = m % 60;
    if (!h) return "あと" + mm + "分";
    return mm ? "あと" + h + "時間" + mm + "分" : "あと" + h + "時間";
  };
  const nowSpan = (m) => '<span class="now' + (m >= 60 ? " long" : "") + '">' + leftText(m) + "</span>";
  // 「明日」または「11月24日(月)」
  const dayLabel = (iso, today) => {
    if (iso === addDays(today, 1)) return "明日";
    const t = new Date(iso + "T00:00:00Z");
    return (t.getUTCMonth() + 1) + "月" + t.getUTCDate() + "日(" + "日月火水木金土"[t.getUTCDay()] + ")";
  };

  // ---------- お知らせ ----------
  // 2か所から読む(どちらか片方だけでもよい):
  //  ・Google スプレッドシート(C.noticesCsv): 列「場所 / お知らせ / 表示開始 / 表示終了」。
  //    表示開始・終了が空なら、いつでも出す。日付の範囲外の行は出さない(期限が来たら自動で消える)。
  //  ・docs/notices.txt: 1行に「場所: 文章」。# で始まる行は説明。
  // 場所は 全部 / 米多比 / 青柳 / コスモス館 / 古賀駅(「青柳、コスモス館」のように複数も可)。
  let notices = [];
  const forHere = (place) => {
    const areas = String(place).split(/[,、・\s]+/).filter(Boolean);
    return areas.includes("全部") || areas.includes(C.area);
  };
  // "2026/11/20" "2026-11-20" "2026年11月20日" などを "2026-11-20" に(時刻が付いていても日付だけ見る)
  const normDate = (s) => {
    const m = String(s || "").match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/);
    return m ? m[1] + "-" + m[2].padStart(2, "0") + "-" + m[3].padStart(2, "0") : "";
  };
  // CSV を行×列の配列に(「"」で囲んだ中のカンマや改行もそのまま扱う)
  const parseCsv = (text) => {
    const rows = []; let row = [], cell = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
        else if (c === '"') q = false;
        else cell += c;
      } else if (c === '"') q = true;
      else if (c === ",") { row.push(cell); cell = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(cell); rows.push(row); row = []; cell = "";
      } else cell += c;
    }
    if (cell || row.length) { row.push(cell); rows.push(row); }
    return rows;
  };
  const fromSheet = (text) => {
    const today = jstNow().date, list = [];
    parseCsv(text).slice(1).forEach(([place, msg, from, to]) => {   // 1行目は見出し
      if (!msg || !msg.trim() || !forHere(place || "")) return;
      const f = normDate(from), t = normDate(to);
      if ((f && today < f) || (t && today > t)) return;
      list.push(msg.trim());
    });
    return list;
  };
  const fromText = (text) => {
    const list = [];
    text.split(/\r?\n/).forEach((line) => {
      line = line.trim();
      if (!line || line.startsWith("#")) return;
      const m = line.match(/^([^:：]+)[:：]\s*(.+)$/);
      if (m && forHere(m[1])) list.push(m[2]);
    });
    return list;
  };
  const get = (url, parse) => fetch(url + (url.includes("?") ? "&" : "?") + "t=" + Date.now(), { cache: "no-store" })
    .then((r) => (r.ok ? r.text() : Promise.reject(r.status))).then(parse);
  let sheetList = [], textList = [];
  function loadNotices() {
    const jobs = [get("notices.txt", fromText).then((l) => { textList = l; }).catch(() => {})];
    // 読めなかったときは前のお知らせのまま(ネットが一瞬切れても消えない)
    if (C.noticesCsv) jobs.push(get(C.noticesCsv, fromSheet).then((l) => { sheetList = l; }).catch(() => {}));
    Promise.all(jobs).then(() => { notices = sheetList.concat(textList); render(); });
  }
  const noticeHtml = (extra) => {
    const items = (extra ? [extra] : []).concat(notices);
    if (!items.length) return "";
    return '<table class="msg">' + items.map((s) =>
      "<tr><th>お知らせ</th><td>" + esc(s) + "</td></tr>").join("") + "</table>";
  };

  // ---------- コガバス(青柳・コスモス館・JR古賀駅) ----------
  // 次に運行がある日の始発(明日以降、最大7日先まで)
  function nextFirstKoga(today) {
    for (let i = 1; i <= 7; i++) {
      const d = addDays(today, i);
      const list = data.days[d];
      if (list && list.length) {
        const [sec, r, h] = list[0];
        return { label: dayLabel(d, today), time: fmt(sec), dest: data.heads[h] };
      }
    }
    return null;
  }

  // その日のバスが終わったときに出す行
  function endRow(today, cols) {
    const f = nextFirstKoga(today);
    const next = f ? f.label + "の始発は " + f.time + "(" + esc(f.dest) + "行)です" : "";
    return '<tr class="endmsg"><td class="gyo txtct" colspan="' + cols + '">' +
      '<span class="yki">本日の運行は終了しました</span><br/><span class="kiy">' + next + "</span></td></tr>";
  }
  // 今日のダイヤと、深夜をまたぐ前日のダイヤ(25:10 など)の両方から、今より後の発車を集める
  function nextKoga(now, limit) {
    const found = [];
    (data.days[now.date] || []).forEach(([sec, r, h]) => {
      if (sec >= now.sec) found.push([sec, r, h]);
    });
    (data.days[addDays(now.date, -1)] || []).forEach(([sec, r, h]) => {
      if (sec >= 86400 && sec - 86400 >= now.sec) found.push([sec - 86400, r, h]);
    });
    found.sort((a, b) => a[0] - b[0]);
    return found.slice(0, limit).map(([sec, r, h]) => ({
      time: fmt(sec), route: data.routes[r], dest: data.heads[h],
      minutes: Math.max(0, Math.floor((sec - now.sec) / 60)),
    }));
  }

  function kogaRows(deps, count, end) {
    let html = end || "";                     // その日のバスが終わったら、先頭に案内の行
    if (end) count -= 1;
    deps.slice(0, count).forEach((d) => {
      html += '<tr><td class="gyo bin">' + esc(d.route) + "</td>" +
        '<td class="gyo"><span class="yki">' + esc(d.dest) + '</span><br/><span class="kiy">&#12288;</span></td>' +
        '<td class="gyo txtct"><span class="jkn">' + d.time + "</span><br/>" + nowSpan(d.minutes) + "</td></tr>";
    });
    for (let i = deps.length; i < count; i++) {
      html += '<tr class="pad"><td class="gyo bin"></td><td class="gyo"></td><td class="gyo txtct"></td></tr>';
    }
    return html;
  }

  function kogaList(deps, count, side, end) {
    return '<table class="list ' + side + '"><tr><th class="i_bin">路線</th><th class="i_yk">行先</th>' +
      '<th class="i_jkn">所定時刻 発車まで</th></tr>' + kogaRows(deps, count, end) + "</table>";
  }

  function renderKoga() {
    const now = jstNow();
    const wide = C.template === 18;
    const perCol = wide ? 5 : 15, cols = wide ? 2 : 1;
    const deps = nextKoga(now, perCol * cols);
    const head = '<tr><th colspan="' + cols + '" class="header_title">' +
      '<div class="text_title"><span class="brand">コガバス</span>接近情報<br />' + esc(C.stop) + "</div>" +
      '<div class="text_time">' + now.hhmm + " 現在の状況</div></th></tr>";
    const end = deps.length ? "" : endRow(now.date, 3);
    const body = wide
      ? '<tr><td class="va_top">' + kogaList(deps.slice(0, perCol), perCol, "left", end) + "</td>" +
        '<td class="va_top">' + kogaList(deps.slice(perCol), perCol, "right") + "</td></tr>"
      : '<tr><td class="va_top">' + kogaList(deps, perCol, "left", end) + "</td></tr>";
    let note = "";
    if (now.date > data.last) note = '<div class="credit">※ 時刻表データの期限が切れています。新しい時刻表に更新してください。</div>';
    board.innerHTML = '<div class="nnr t' + C.template + '" data-w="' + (wide ? 1920 : 1280) + '">' +
      '<table class="disp">' + head + body + "</table>" + noticeHtml() + note +
      '<div class="credit">時刻表データ出典: 古賀市「コガバス」GTFS-JP(CC BY 4.0)</div></div>';
  }

  // ---------- 米多比(西鉄バス → JR古賀駅 乗り継ぎ案内) ----------
  // その日のダイヤ(土日と holidays.csv の日は土休日)
  const diagramOf = (iso) => {
    const wd = new Date(iso + "T00:00:00Z").getUTCDay();
    return wd === 0 || wd === 6 || data.holidays.includes(iso) ? "土休日" : "平日";
  };

  function renderYatabi() {
    const now = jstNow();
    const diagram = diagramOf(now.date);
    const transfer = C.transfer * 60;
    const buses = data.buses.filter((b) => b[0] === diagram && b[1] >= now.sec).slice(0, 3);
    const trainTd = (dir, arr) => {
      const t = data.trains.find((x) => x[0] === dir && x[1] === diagram && x[2] >= arr + transfer);
      if (!t) return '<td class="gyo txtct"><span class="now">接続する電車はありません</span></td>';
      const cls = /特急|急行/.test(t[3]) ? " express" : /快速/.test(t[3]) ? " rapid" : "";
      const kind = t[3] ? '<span class="op' + cls + '">' + esc(t[3]) + "</span>" : "";
      return '<td class="gyo txtct">' + kind + '<span class="jkn">' + fmt(t[2]) + "</span><br/>" +
        '<span class="now">' + esc(t[4]) + "行 到着後" + Math.floor((t[2] - arr) / 60) + "分</span></td>";
    };
    let rows = "";
    buses.forEach((b, i) => {
      const m = Math.max(0, Math.floor((b[1] - now.sec) / 60));
      rows += '<tr class="' + (i === 0 ? "first" : "next") + '">' +
        '<td class="gyo txtct"><span class="jkn">' + fmt(b[1]) + "</span><br/>" + nowSpan(m) + "</td>" +
        '<td class="gyo txtct"><span class="jkn">' + fmt(b[2]) + "</span><br/>" +
        '<span class="kiy">' + esc(b[3] || "JR古賀駅") + "着</span></td>" +
        C.directions.map((d) => trainTd(d, b[2])).join("") + "</tr>";
    });
    const ncol = 2 + C.directions.length;
    if (!buses.length) {
      // 次にバスがある日の始発(明日以降、最大7日先まで)
      let next = "";
      for (let i = 1; i <= 7 && !next; i++) {
        const d = addDays(now.date, i);
        const b = data.buses.find((x) => x[0] === diagramOf(d));
        if (b) next = dayLabel(d, now.date) + "の始発は " + fmt(b[1]) + "(" + fmt(b[2]) + " " + esc(b[3] || "JR古賀駅") + "着)です";
      }
      rows += '<tr class="first endmsg"><td class="gyo txtct" colspan="' + ncol + '">' +
        '<span class="yki">本日のバスは終了しました</span><br/><span class="kiy">' + next + "</span></td></tr>";
    }
    for (let i = Math.max(buses.length, 1); i < 3; i++) {
      rows += '<tr class="next pad">' + '<td class="gyo"></td>'.repeat(ncol) + "</tr>";
    }
    const ths = '<th>米多比発 発車まで</th><th>古賀駅着</th>' +
      C.directions.map((d) => "<th>JR " + esc(C.labels[d] || d) + "</th>").join("");
    const notice = noticeHtml(data.sample ? "サンプルデータを表示中です(実際の時刻ではありません)" : "");
    board.innerHTML = '<div class="nnr t18 yatabi" data-w="1920"><table class="disp">' +
      '<tr><th class="header_title"><div class="text_title"><span class="brand">乗り継ぎ案内</span>' +
      esc(C.stop) + " → JR古賀駅</div>" +
      '<div class="text_time">' + now.hhmm + " 現在の状況</div></th></tr>" +
      '<tr><td class="va_top"><table class="list"><tr>' + ths + "</tr>" + rows + "</table>" + notice +
      "</td></tr></table></div>";
  }

  // ---------- 画面に合わせて拡大・縮小(いつも1画面に収める) ----------
  // バスの入っている行(とお知らせ)が全部見える範囲で、できるだけ大きく表示する。
  // 西鉄に合わせて足している空の行(.pad)は、入りきらなければ表示しない。
  function fit() {
    const el = board.querySelector(".nnr");
    if (!el) return;
    const designW = Number(el.dataset.w) || 1920;
    el.style.transform = "none";
    el.style.width = designW + "px";
    el.querySelectorAll("tr.pad").forEach((r) => { r.style.display = ""; });
    const top = el.getBoundingClientRect().top;
    let needH = 0;
    el.querySelectorAll(".header_title, tr:not(.pad) > td.gyo, td .msg").forEach((c) => {
      needH = Math.max(needH, c.getBoundingClientRect().bottom - top);
    });
    if (!needH) return;
    // 表の下に付くお知らせ・出典は空の行の下にあるので、高さだけ別に足す(空の行を消すと上に詰まる)
    let creditH = 0;
    el.querySelectorAll(":scope > .credit, :scope > .msg").forEach((c) => {
      const cs = getComputedStyle(c);
      creditH += c.offsetHeight + parseFloat(cs.marginTop) + parseFloat(cs.marginBottom);
    });
    needH += 8 + creditH;                              // 8 は表の下の枠線のぶん
    const s = Math.min(window.innerWidth / designW, window.innerHeight / needH);
    el.style.width = window.innerWidth / s + "px";     // 拡大・縮小したあとも横幅いっぱいに
    const limit = window.innerHeight / s - creditH - 8;
    el.querySelectorAll("tr.pad").forEach((r) => {
      if (r.getBoundingClientRect().bottom - top > limit) r.style.display = "none";
    });
    el.style.transform = "scale(" + s + ")";
  }

  function render() {
    if (!data) return;
    if (C.kind === "yatabi") renderYatabi(); else renderKoga();
    fit();
  }

  // ---------- 西鉄バスナビと交互に表示(青柳・コスモス館・JR古賀駅) ----------
  // URLを開くと表示用のウィンドウを開き、その中身を「このページ(?display=1)」⇔
  // 「西鉄バスナビ(元のURLのまま)」と交互に移動させる。西鉄のページは埋め込まず、一切変更しない。
  function startSwitcher() {
    const params = new URLSearchParams(location.search);
    if (C.kind !== "koga" || !C.nnr || params.get("display")) return;

    const panel = document.createElement("div");
    panel.id = "sw-panel";
    document.body.appendChild(panel);
    const selfUrl = location.origin + location.pathname + "?display=1";
    let win = null, phase = "", due = 0, waiting = false, waitUntil = 0;

    const show = (html, handlers) => {
      panel.className = "";
      panel.innerHTML = '<div class="box">' + html + "</div>";
      Object.entries(handlers).forEach(([id, fn]) => { panel.querySelector("#" + id).onclick = fn; });
    };
    const close = () => { panel.className = "hidden"; };
    const showStart = () => show(
      "<h2>西鉄バスと切り替えて表示</h2><p>「表示開始」を押すと新しいウィンドウが開き、コガバスと西鉄バスの案内が" +
      C.sec + "秒ごとに切り替わります。</p><p>開いたウィンドウで <b>F11</b> を押すと全画面になります。</p>" +
      '<button id="sw-start">表示開始</button><button id="sw-close" class="sub">このまま見る</button>',
      { "sw-start": start, "sw-close": close });
    const showBlocked = () => show(
      "<h2>ポップアップを許可してください</h2><p>表示用のウィンドウを開けませんでした。" +
      "<b>このパソコンで最初の1回だけ</b>、次の設定をしてください。</p>" +
      "<p>アドレスバーの右に出ている <b>ポップアップのアイコン</b> を押し、「<b>常に許可する</b>」を選んで「完了」。" +
      "<br>次からは、URLを開くだけで自動で始まります。</p>" +
      '<button id="sw-start">今すぐ表示開始</button><button id="sw-close" class="sub">このまま見る</button>',
      { "sw-start": start, "sw-close": close });
    const showRunning = () => show(
      "<h2>表示中です</h2><p><b>このウィンドウは閉じないでください。</b>閉じると切り替えが止まります。</p>" +
      "<p>表示用のウィンドウで <b>F11</b> を押すと全画面になります。</p>" +
      '<p style="font-size:15px;color:#666">長時間つけておくパソコンでは、Chrome の設定 →「パフォーマンス」→' +
      "「常にアクティブにしておくサイト」に <b>" + location.hostname + "</b> を追加しておくと安心です。</p>" +
      '<button id="sw-stop" class="sub">停止する</button>',
      { "sw-stop": stop });

    const go = (p) => {
      phase = p;
      if (p === "koga") {
        win.location.href = selfUrl;
        waiting = true; waitUntil = Date.now() + 15000;       // 表示されるまで待つ(最大15秒)
      } else {
        win.location.href = C.nnr;
        waiting = false; due = Date.now() + (C.sec + 1) * 1000; // 読み込みの1秒ぶん長めに
      }
    };
    const tick = () => {
      if (!win) return;
      if (win.closed) { stop(); return; }
      const now = Date.now();
      if (phase === "koga" && waiting) {
        let ok = false;
        try { ok = !!win.document.querySelector(".nnr"); } catch (e) { /* まだ西鉄のページ */ }
        if (ok || now > waitUntil) { waiting = false; due = now + C.sec * 1000; }
        return;
      }
      if (now >= due) go(phase === "koga" ? "nnr" : "koga");
    };
    // 裏に回っても遅くならない Web Worker の時計で数える
    const worker = new Worker(URL.createObjectURL(new Blob(
      ["setInterval(() => postMessage(0), 200);"], { type: "text/javascript" })));
    worker.onmessage = tick;

    function start() {
      win = window.open(selfUrl, "koga-display",
        "popup=yes,left=0,top=0,width=" + screen.availWidth + ",height=" + screen.availHeight);
      if (!win) { showBlocked(); return; }
      phase = "koga"; waiting = true; waitUntil = Date.now() + 15000;
      showRunning();
    }
    function stop() {
      if (win && !win.closed) win.close();
      win = null; phase = "";
      showStart();
    }
    start();          // URLを開いたら自動で始める(許可されていなければ案内を出す)
  }

  // ---------- 起動 ----------
  function load() {
    fetch(C.data + "?t=" + Date.now(), { cache: "no-store" })
      .then((r) => r.json())
      .then((j) => { data = j; render(); })
      .catch(() => { if (!data) board.innerHTML = '<div class="nnr"><div class="empty">時刻表を読み込めませんでした</div></div>'; });
  }
  load();
  loadNotices();
  setInterval(render, REFRESH_MS);
  setInterval(load, 6 * 3600 * 1000);   // 時刻表の更新(Push)を6時間ごとに取り込む
  setInterval(loadNotices, 60 * 1000);  // お知らせは1分ごとに読み直す
  window.addEventListener("resize", fit);
  startSwitcher();
})();
