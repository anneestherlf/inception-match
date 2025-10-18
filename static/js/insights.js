// Chat logic moved from insights.html
document.addEventListener('DOMContentLoaded', function(){
    const suggestions = document.querySelectorAll('.suggestion-btn');
    const input = document.querySelector('.message-input');
    const sendBtn = document.querySelector('.send-message-btn');
    const messagesContainer = document.querySelector('.messages-container');

    function appendMessage(text, who, extraClass=''){
        const el = document.createElement('div');
        el.className = `msg ${who} ${extraClass}`.trim();
        el.textContent = text;
        messagesContainer.appendChild(el);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return el;
    }

    async function sendMessage(text){
        if(!text) return;
        appendMessage(text, 'user');
        input.value = '';

        // loading bubble
        const loading = document.createElement('div');
        loading.className = 'msg bot loading';
        loading.textContent = '...';
        messagesContainer.appendChild(loading);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try{
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            });
            const data = await resp.json();
            messagesContainer.removeChild(loading);

            if(resp.ok && data.answer){
                const botEl = appendMessage(data.answer, 'bot');
                if(Array.isArray(data.sources) && data.sources.length){
                    const srcList = document.createElement('div');
                    srcList.className = 'bot-sources';
                    data.sources.forEach(s => {
                        const a = document.createElement('a');
                        a.href = s.link;
                        a.target = '_blank';
                        a.rel = 'noopener noreferrer';
                        a.textContent = s.title || s.link;
                        a.className = 'bot-source-link';
                        srcList.appendChild(a);
                    });
                    messagesContainer.appendChild(srcList);
                }
            } else if(data.error){
                appendMessage('Erro: ' + data.error, 'bot');
            } else {
                appendMessage('Desculpe, não consegui obter resposta.', 'bot');
            }
        }catch(err){
            messagesContainer.removeChild(loading);
            appendMessage('Erro de conexão ao enviar a mensagem.', 'bot');
        }
    }

    if(suggestions.length && input){
        suggestions.forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.textContent.trim();
                input.value = text;
                input.focus();

                // small visual feedback
                btn.classList.add('suggestion-active');
                setTimeout(() => btn.classList.remove('suggestion-active'), 250);
            });
        });
    }

    if(sendBtn && input){
        sendBtn.addEventListener('click', () => sendMessage(input.value.trim()));

        input.addEventListener('keydown', (e) => {
            if(e.key === 'Enter' && !e.shiftKey){
                e.preventDefault();
                sendMessage(input.value.trim());
            }
        });
    }
});
