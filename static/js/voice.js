var recognition = null, isRecording = false, currentTopic = '';

function setTopic(topic) {
    currentTopic = topic;
    document.getElementById('topicHint').textContent = '当前话题：' + topic;
}

function toggleRecord() {
    if (isRecording) { stopRecord(); return; }

    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        document.getElementById('statusText').textContent = '此浏览器不支持语音，请用输入框替代';
        return;
    }

    try {
        recognition = new SR();
    } catch(e) {
        document.getElementById('statusText').textContent = '语音功能不可用，请用输入框';
        return;
    }

    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        isRecording = true;
        var btn = document.getElementById('recordBtn');
        btn.textContent = '停止'; btn.style.background = 'var(--red)';
        document.getElementById('micIcon').textContent = '🔴';
        document.getElementById('statusText').textContent = '正在录音...';
    };

    recognition.onresult = function(event) {
        var text = event.results[0][0].transcript;
        document.getElementById('spokenText').textContent = text;
        document.getElementById('resultCard').style.display = 'block';
        document.getElementById('correction').innerHTML = '<span class="mascot-hamster">🐹</span> AI正在纠错...';
        sendForCorrection(text);
    };

    recognition.onerror = function(e) {
        isRecording = false; resetUI();
        document.getElementById('statusText').textContent = '录音失败: ' + (e.error||'未知错误');
    };

    recognition.onend = function() { isRecording = false; resetUI(); };

    try { recognition.start(); } catch(e) {
        isRecording = false; resetUI();
        document.getElementById('statusText').textContent = '无法启动录音，请检查麦克风权限';
    }
}

function stopRecord() {
    try { if (recognition) recognition.stop(); } catch(e) {}
    isRecording = false;
    resetUI();
}

function resetUI() {
    var btn = document.getElementById('recordBtn');
    btn.textContent = '开始录音'; btn.style.background = '';
    document.getElementById('micIcon').textContent = '🎤';
    document.getElementById('statusText').textContent = '点击开始录音，或用下方输入框打字练习';
}

// 输入框替代方案
function submitTextForCorrection() {
    var input = document.getElementById('textInput');
    var text = input.value.trim();
    if (!text) return;
    document.getElementById('spokenText').textContent = text;
    document.getElementById('resultCard').style.display = 'block';
    document.getElementById('correction').innerHTML = '<span class="mascot-hamster">🐹</span> AI正在纠错...';
    sendForCorrection(text);
    input.value = '';
}

function sendForCorrection(text) {
    var topicCtx = currentTopic ? ' 话题：' + currentTopic : '';
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: '我刚刚说了/写了这句英语，请帮我纠错：\n"' + text + '"\n' + topicCtx + '\n\n从发音、语法、用词方面给建议和润色版。简洁回复。',
            history: []
        })
    }).then(function(r){ return r.json(); }).then(function(d){
        document.getElementById('correction').innerHTML = d.reply.replace(/\n/g, '<br>');
        updateCostBubble();
    });
}
