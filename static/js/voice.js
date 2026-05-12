var recognition = null, isRecording = false, oralHistory = [], micSupported = false;

function initOral() {
    // 检测语音支持
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) {
        try { var test = new SR(); micSupported = true; } catch(e) {}
    }
    if (!micSupported) {
        document.getElementById('recordBtn').style.display = 'none';
        document.getElementById('chatInput').style.marginLeft = '0';
    }

    document.getElementById('chatArea').innerHTML =
        '<div class="chat-msg assistant"><div class="bubble">🎙️ 欢迎来到口语练习！<br><br>' +
        (micSupported ? '点🎤录音或者说英语，AI给你反馈~' : '在下方输入框打字练习英语，AI帮你纠错~') +
        '<br><br>也可以点上面按钮让我给你稿子照着念 👆</div></div>';
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
        body: JSON.stringify({message: '我练习了口语，内容是：\n' + text + '\n请从发音技巧、语法、用词方面给反馈。简洁回复。', history: oralHistory})
    }).then(function(r){ return r.json(); }).then(function(d){
        hideLoading();
        addBubble('assistant', d.reply);
        oralHistory.push({role:'assistant', content:d.reply});
        updateCostBubble();
    });
}

function toggleRecord() {
    if (!micSupported) return;
    if (isRecording) { stopRecord(); return; }

    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    try { recognition = new SR(); } catch(e) { return; }

    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    var timeout = setTimeout(function() {
        if (!isRecording) {
            try { recognition.stop(); } catch(e) {}
            spawnDanmaku('麦克风超时，请打字输入', 'wrong');
        }
    }, 5000);

    recognition.onstart = function() {
        clearTimeout(timeout); isRecording = true;
        var btn = document.getElementById('recordBtn');
        btn.textContent = '⏹'; btn.style.background = 'var(--red)';
    };

    recognition.onresult = function(event) {
        var text = event.results[0][0].transcript;
        document.getElementById('chatInput').value = text;
        sendOralMsg();
    };

    recognition.onerror = function(e) { isRecording = false; resetUI(); };
    recognition.onend = function() { isRecording = false; resetUI(); };

    try { recognition.start(); } catch(e) { isRecording = false; resetUI(); }
}

function stopRecord() { try { recognition.stop(); } catch(e) {} isRecording = false; resetUI(); }

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
