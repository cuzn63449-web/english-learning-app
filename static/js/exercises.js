var chatHistory = [], selectedGroup = '';

function init() {
    fetch('/api/stats').then(function(r){ return r.json(); }).then(function(d){
        document.getElementById('learnedCount').textContent = '已学'+d.mastered+'词';
    });
    loadGroups();
}

function loadGroups() {
    fetch('/api/groups').then(function(r){ return r.json(); }).then(function(data){
        var sel = document.getElementById('groupSelect');
        data.forEach(function(g){
            var opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = '组'+g.id+' ('+g.date+' | '+g.count+'词)';
            sel.appendChild(opt);
        });
    });
}

function changeGroup() {
    selectedGroup = document.getElementById('groupSelect').value;
    if (selectedGroup) {
        addBubble('assistant', '已选择组'+selectedGroup+'的词汇，接下来出题将使用这些词~');
    } else {
        addBubble('assistant', '已切换为智能模式，AI会自动选择你正在学的词~');
    }
}
    var area = document.getElementById('chatArea');
    area.innerHTML = '<div class="chat-msg assistant"><div class="bubble">你好！我是你的AI英语助教 🐹<br><br>我可以：<br>📝 用你学过的词出选择题<br>📖 生成阅读理解<br>✍️ 出写作题并批改<br>🔍 分析文章<br><br>直接告诉我你想做什么，或者点下面的快捷按钮 👇</div></div>';
}

function quickSend(msg) {
    document.getElementById('chatInput').value = msg;
    sendMsg();
}

function sendMsg() {
    var input = document.getElementById('chatInput');
    var msg = input.value.trim();
    if (!msg) return;
    input.value = '';

    addBubble('user', msg);
    showLoading();
    fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: msg, history: chatHistory, group_id: selectedGroup})
    }).then(function(r){ return r.json(); }).then(function(d){
        hideLoading();
        addBubble('assistant', d.reply);
        chatHistory.push({role:'user', content:msg});
        chatHistory.push({role:'assistant', content:d.reply});
        updateCostBubble();
    });
}

function addBubble(role, text) {
    var div = document.createElement('div');
    div.className = 'chat-msg ' + role;
    div.innerHTML = '<div class="bubble">' + renderContent(text) + '</div>';
    document.getElementById('chatArea').appendChild(div);
    div.scrollIntoView({behavior: 'smooth'});
}

function renderContent(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre style="background:rgba(0,0,0,0.05);padding:10px;border-radius:8px;overflow-x:auto;font-size:13px">$2</pre>')
        .replace(/`(.+?)`/g, '<code style="background:rgba(0,0,0,0.06);padding:2px 6px;border-radius:4px">$1</code>');
}

init();
