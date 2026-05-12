var recognition = null, isRecording = false, currentTopic = '';

function setTopic(topic) {
    currentTopic = topic;
    document.getElementById('topicHint').textContent = '当前话题：' + topic;
}

function toggleRecord() {
    if (isRecording) { stopRecord(); return; }

    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert('你的浏览器不支持语音识别，请用Chrome或Edge');
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        isRecording = true;
        document.getElementById('recordBtn').textContent = '停止';
        document.getElementById('recordBtn').style.background = 'var(--red)';
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

    recognition.onerror = function(event) {
        isRecording = false;
        resetUI();
        document.getElementById('statusText').textContent = '录音失败，请重试';
    };

    recognition.onend = function() { isRecording = false; resetUI(); };
    recognition.start();
}

function stopRecord() {
    if (recognition) { recognition.stop(); }
    isRecording = false;
    resetUI();
}

function resetUI() {
    document.getElementById('recordBtn').textContent = '开始录音';
    document.getElementById('recordBtn').style.background = '';
    document.getElementById('micIcon').textContent = '🎤';
    document.getElementById('statusText').textContent = '点击开始录音';
}

function sendForCorrection(text) {
    var topicCtx = currentTopic ? ' 话题：' + currentTopic : '';
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: '我刚刚说了这句英语，请帮我纠错：\n"' + text + '"\n' + topicCtx + '\n\n请从发音可能的问题（注意这是语音识别转写的，可能有识别误差）、语法、用词、流利度方面给建议，并给一个改进版。用鼓励的语气，不要太长。',
            history: []
        })
    }).then(function(r){ return r.json(); }).then(function(d){
        document.getElementById('correction').innerHTML = d.reply.replace(/\n/g, '<br>');
        updateCostBubble();
    });
}
