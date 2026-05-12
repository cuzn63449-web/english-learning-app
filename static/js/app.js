// === 通用工具 ===

function showToast(msg, type) {
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast ' + (type || '') + ' show';
    setTimeout(function(){ t.className = 'toast'; }, 1200);
}

function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// === 网感鼓励语 ===
var encouragements = {
    correct: [
        "这个词已经是你的人了😏",
        "绝绝子！",
        "配享太庙！",
        "建议直接保研🎓",
        "拿捏了🤏",
        "这词见你都要绕道走",
        "稳如老狗！",
        "你已经next level了",
        "属于是降维打击了",
        "这不就信手拈来？"
    ],
    wrong: [
        "下次一定！",
        "它认识你你不认识它？",
        "再看看，马上拿下💪",
        "问题不大，再来！",
        "这个确实有点东西，再认认",
        "没关系，主打一个循序渐进"
    ],
    streak: [
        "连续学习第{0}天！你是卷王本王👑",
        "第{0}天了，这个学习状态我respect",
        "已经连续{0}天，这不比刷短视频强？"
    ]
};

function randomEncourage(list) {
    return list[Math.floor(Math.random() * list.length)];
}

// === API花费监控 ===
function updateCostBubble() {
    fetch('/api/cost').then(function(r){ return r.json(); }).then(function(d){
        document.getElementById('costAmount').textContent = 'AI ¥' + d.total.toFixed(3);
        document.getElementById('costDetail').textContent =
            '本月 ¥' + d.month.toFixed(3) + ' | 共' + d.calls + '次 | 预算¥' + d.budget;
    });
}
updateCostBubble();

// === 弹幕式鼓励 ===
function spawnDanmaku(msg, type) {
    var el = document.createElement('div');
    el.textContent = msg;
    el.className = 'danmaku ' + (type || '');
    el.style.left = '60%';
    el.style.top = (15 + Math.random() * 45) + '%';
    document.body.appendChild(el);
    el.addEventListener('animationend', function(){ el.remove(); });
}

// === 可爱小动物 ===
function spawnCuteToast(msg, type) {
    var mascot = type === 'success' ? '🐹' : '🐱';
    var t = document.getElementById('toast');
    t.innerHTML = '<span class="toast-mascot">' + mascot + '</span>' + msg;
    t.className = 'toast ' + (type || '') + ' show';
    setTimeout(function(){ t.className = 'toast'; }, 1200);
}

function spawnFloatMascot() {
    var el = document.createElement('div');
    var mascots = ['🐹', '🐱', '🌸', '💫', '🫧'];
    el.textContent = mascots[Math.floor(Math.random() * mascots.length)];
    el.className = 'float-mascot';
    el.style.top = (10 + Math.random() * 60) + '%';
    el.style.animationDuration = (5 + Math.random() * 6) + 's';
    document.body.appendChild(el);
    el.addEventListener('animationend', function(){ el.remove(); });
}

function spawnConfetti() {
    var emojis = ['🌟', '✨', '💖', '🎀', '🌸', '💫', '🐹', '🐱'];
    for (var i = 0; i < 8; i++) {
        var el = document.createElement('div');
        el.textContent = emojis[Math.floor(Math.random() * emojis.length)];
        el.className = 'confetti';
        el.style.left = (10 + Math.random() * 80) + '%';
        el.style.top = (10 + Math.random() * 50) + '%';
        el.style.animationDelay = (Math.random() * 0.3) + 's';
        document.body.appendChild(el);
        el.addEventListener('animationend', function(){ el.remove(); });
    }
}

// 偶尔飘过小可爱（30%概率）
if (Math.random() < 0.3) {
    setTimeout(spawnFloatMascot, 3000);
    setInterval(function(){
        if (Math.random() < 0.2) spawnFloatMascot();
    }, 25000);
}

// === 按钮缩放动画 ===
document.addEventListener('click', function(e) {
    var btn = e.target.closest('.btn');
    if (btn) {
        btn.classList.add('press-anim');
        setTimeout(function(){ btn.classList.remove('press-anim'); }, 200);
    }
});
