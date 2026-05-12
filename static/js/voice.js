var recognition = null, isRecording = false, oralHistory = [];

function initOral() {
    var area = document.getElementById('chatArea');
    area.innerHTML = '<div class="chat-msg assistant"><div class="bubble">🎙️ 欢迎来到口语练习！<br><br>点下面按钮让我给你一段稿子照着念，或者直接点🎤录音说英语，AI会给你反馈~</div></div>';
}

function quickOral(msg) {
    addBubble('user', msg);
    showLoading();
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg, history: oralHistory})
    }).then(function(r){ return r.json(); }).then(function(d){
        hideLoading();
        addBubble('assistant', d.reply);
        oralHistory.push({role:'user', content:msg});
        oralHistory.push({role:'assistant', content:d.reply});
        updateCostBubble();
    });
}

function sendOralMsg() {
    var input = document.getElementById('chatInput');
    var text = input.value.trim();
    if (!text) return;
    input.value = '';
    addBubble('user', text);
    oralHistory.push({role:'user', content:text});
    showLoading();
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: '我练习了口语，内容是：\n' + text + '\n请从发音技巧、语法、用词方面给反馈和建议。像口语教练一样对话。', history: oralHistory})
    }).then(function(r){ return r.json(); }).then(function(d){
        hideLoading();
        addBubble('assistant', d.reply);
        oralHistory.push({role:'assistant', content:d.reply});
        updateCostBubble();
    });
}

function toggleRecord() {
    if (isRecording) { stopRecord(); return; }

    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        var input = document.getElementById('chatInput');
        input.placeholder = '语音不可用，请打字输入...';
        return;
    }

    try { recognition = new SR(); } catch(e) { return; }

    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        isRecording = true;
        var btn = document.getElementById('recordBtn');
        btn.textContent = '⏹'; btn.style.background = 'var(--red)';
    };

    recognition.onresult = function(event) {
        var text = event.results[0][0].transcript;
        document.getElementById('chatInput').value = text;
        sendOralMsg();
    };

    recognition.onerror = function(e) {
        isRecording = false; resetUI();
        document.getElementById('chatInput').placeholder = '录音失败，请打字...';
    };

    recognition.onend = function() { isRecording = false; resetUI(); };

    try { recognition.start(); } catch(e) { isRecording = false; resetUI(); }
}

function stopRecord() {
    try { if (recognition) recognition.stop(); } catch(e) {}
    isRecording = false; resetUI();
}

function resetUI() {
    var btn = document.getElementById('recordBtn');
    btn.textContent = '🎤'; btn.style.background = '';
}

function addBubble(role, text) {
    var div = document.createElement('div');
    div.className = 'chat-msg ' + role;
    div.innerHTML = '<div class="bubble">' + text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>') + '</div>';
    document.getElementById('chatArea').appendChild(div);
    div.scrollIntoView({behavior: 'smooth'});
}

initOral();
