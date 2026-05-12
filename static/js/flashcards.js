// === 闪卡学习 ===
var words = [], currentIdx = 0, counts = {correct:0, fuzzy:0, wrong:0};
var currentWordId = null, cardFlipped = false, waitingForTap = false;
var currentLevel = '考研';

function switchLevel(level) {
    currentLevel = level;
    var btns = document.querySelectorAll('#levelBar .btn');
    btns.forEach(function(b,i){
        if (b.textContent === level) { b.className = 'btn btn-sm btn-primary'; }
        else { b.className = 'btn btn-sm btn-outline'; }
    });
    startStudy();
}

function startStudy() {
    document.getElementById('sessionStats').style.display = 'none';
    document.getElementById('noWords').style.display = 'none';
    counts = {correct:0, fuzzy:0, wrong:0};
    currentIdx = 0;
    cardFlipped = false;
    waitingForTap = false;
    showLoading();
    fetch('/api/study/start?level='+encodeURIComponent(currentLevel)).then(function(r){ return r.json(); }).then(function(data){
        hideLoading();
        if (data.length === 0) {
            document.getElementById('studyCard').style.display = 'none';
            document.getElementById('noWords').style.display = 'block';
            return;
        }
        words = data;
        document.getElementById('studyCard').style.display = 'block';
        showCard(0);
    });
}

function showCard(i) {
    currentIdx = i;
    cardFlipped = false;
    waitingForTap = false;
    var w = words[i];
    currentWordId = w.id || w.word_id;
    var marked = w.is_marked || false;
    var txt = marked ? '★' : '☆';
    var clr = marked ? 'var(--gold)' : '';
    document.getElementById('markBtn1').textContent = txt;
    document.getElementById('markBtn1').style.color = clr;
    document.getElementById('markBtn2').textContent = txt;
    document.getElementById('markBtn2').style.color = clr;
    var card = document.getElementById('flashcard');
    card.classList.remove('flipped', 'flash-correct', 'flash-wrong');
    card.onclick = null;  // 选之前不能翻
    document.getElementById('fcWord').textContent = w.word;
    document.getElementById('fcPhonetic').textContent = w.phonetic || '';
    document.getElementById('fcMeaning').textContent = w.meaning || '';
    document.getElementById('fcExtra').innerHTML = (w.part_of_speech ? '<p><strong>词性:</strong> '+w.part_of_speech+'</p>' : '');
    document.getElementById('progressTag').textContent = (i+1) + '/' + words.length;
    document.getElementById('actionBtns').style.display = 'flex';
    document.getElementById('fcHint').textContent = '👇 选择你认不认识这个词';
}

function flipCard() {
    if (waitingForTap) {
        // 用户点击后进入下一张
        if (currentIdx + 1 < words.length) {
            showCard(currentIdx + 1);
        } else {
            showStats();
        }
        return;
    }
    cardFlipped = !cardFlipped;
    document.getElementById('flashcard').classList.toggle('flipped');
}

function toggleMark() {
    var btn1 = document.getElementById('markBtn1');
    var isMarked = btn1.textContent === '★';
    fetch('/api/study/toggle_mark', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({word_id: currentWordId})
    }).then(function(r){ return r.json(); }).then(function(d){
        var txt = d.marked ? '★' : '☆';
        var clr = d.marked ? 'var(--gold)' : '';
        document.getElementById('markBtn1').textContent = txt;
        document.getElementById('markBtn1').style.color = clr;
        document.getElementById('markBtn2').textContent = txt;
        document.getElementById('markBtn2').style.color = clr;
        spawnDanmaku(d.marked ? '已收藏⭐' : '已取消', 'fuzzy');
    });
}

function speakWord() {
    var word = words[currentIdx].word;
    if ('speechSynthesis' in window) {
        var u = new SpeechSynthesisUtterance(word);
        u.lang = 'en-US'; u.rate = 0.85;
        speechSynthesis.speak(u);
    }
}

function submitResult(result) {
    if (waitingForTap) return;
    counts[result] = (counts[result] || 0) + 1;
    document.getElementById('actionBtns').style.display = 'none';

    var card = document.getElementById('flashcard');
    if (!cardFlipped) flipCard();
    waitingForTap = true;
    card.onclick = flipCard;
    document.getElementById('fcHint').textContent = '👆 点击任意处继续';

    if (result === 'correct') {
        card.classList.add('flash-correct');
        spawnDanmaku(randomEncourage(encouragements.correct), 'correct');
        spawnConfetti();
    } else if (result === 'wrong') {
        card.classList.add('flash-wrong');
        spawnDanmaku(randomEncourage(encouragements.wrong), 'wrong');
    } else {
        spawnDanmaku('差点意思，下次拿下！💪', 'fuzzy');
    }

    fetch('/api/study/result', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({word_id: currentWordId, result: result})
    }).then(function(r){ return r.json(); }).then(function(d){
        console.log('saved', d);
    });
}

function showStats() {
    document.getElementById('studyCard').style.display = 'none';
    document.getElementById('sessionStats').style.display = 'block';
    document.getElementById('ssCorrect').textContent = counts.correct || 0;
    document.getElementById('ssFuzzy').textContent = counts.fuzzy || 0;
    document.getElementById('ssWrong').textContent = counts.wrong || 0;
    updateCostBubble();
}

startStudy();
