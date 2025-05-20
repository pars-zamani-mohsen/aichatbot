class ChatWidget {
    constructor(config) {
        this.customerId = config.customerId;
        this.position = config.position;
        this.apiUrl = config.apiUrl;
        this.container = null;
        this.chatWindow = null;
        this.messageList = null;
        this.isOpen = false;
        this.title = config.title || 'چت آنلاین';
        this.isLoading = false;

        // اضافه کردن تاریخچه چت
        this.chatHistory = [];
        this.loadChatHistory();

        this.isOnline = navigator.onLine;
        this.welcomeMessage = config.welcomeMessage || 'سلام! چطور می‌توانم کمکتان کنم؟';

        this.loadChatHistory();
        this.setupOnlineStatus();
        this.loadMarkdownParser();

        this.draftMessage = '';
        this.isTyping = false;
        this.typingTimeout = null;
        this.maxFileSize = config.maxFileSize || 5 * 1024 * 1024; // 5MB
        this.allowedFileTypes = config.allowedFileTypes || ['image/jpeg', 'image/png', 'image/gif'];

        this.loadEmojiPicker();
        this.loadDraft();

        this.theme = {
            primary: config.theme?.primary || '#0084ff',
            secondary: config.theme?.secondary || '#e3f2fd',
            background: config.theme?.background || '#ffffff',
            text: config.theme?.text || '#000000',
            error: config.theme?.error || '#d32f2f',
            success: config.theme?.success || '#4caf50',
            fontSize: config.theme?.fontSize || '14px',
            fontFamily: config.theme?.fontFamily || 'inherit',
            borderRadius: config.theme?.borderRadius || '10px',
            boxShadow: config.theme?.boxShadow || '0 2px 10px rgba(0,0,0,0.1)'
        };
    }

    async init() {
        this.container = this.createContainer();
        this.chatWindow = this.createChatWindow();
        const titleBar = this.createTitleBar();
        this.messageList = this.createMessageList();
        const input = this.createInput();
        const toggleButton = this.createToggleButton();
        this.chatWindow.appendChild(titleBar);

        this.addStyles();
        this.chatWindow.appendChild(this.messageList);
        this.chatWindow.appendChild(input);
        this.container.appendChild(this.chatWindow);
        this.container.appendChild(toggleButton);
        document.body.appendChild(this.container);

        this.chatWindow.style.display = 'none';

        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter' && e.target.value.trim()) {
                const message = e.target.value.trim();
                e.target.value = '';
                await this.sendMessage(message);
            }
        });

        toggleButton.addEventListener('click', () => this.toggleChat());

        // نمایش تاریخچه چت
        this.chatHistory.forEach(message => {
            this.addMessage(message.text, message.type, false);
        });

        if (this.chatHistory.length === 0) {
            this.addMessage(this.welcomeMessage, 'bot');
        }

        this.applyTheme();
    }

    updateTheme(newTheme) {
        this.theme = {
            ...this.theme,
            ...newTheme
        };
        this.applyTheme();
    }

    applyTheme() {
        const customStyles = `
            .chat-window {
                background-color: ${this.theme.background};
                font-family: ${this.theme.fontFamily};
                font-size: ${this.theme.fontSize};
                border-radius: ${this.theme.borderRadius};
                box-shadow: ${this.theme.boxShadow};
            }

            .chat-title-bar {
                background-color: ${this.theme.primary};
            }

            .chat-message.user {
                background-color: ${this.theme.secondary};
                color: ${this.theme.text};
            }

            .chat-message.bot {
                background-color: ${this.theme.background};
                color: ${this.theme.text};
                border: 1px solid ${this.theme.primary}20;
            }

            .chat-message.error {
                background-color: ${this.theme.error}20;
                color: ${this.theme.error};
            }

            .toggle-button {
                background-color: ${this.theme.primary};
                box-shadow: ${this.theme.boxShadow};
            }

            .send-button {
                background-color: ${this.theme.primary};
            }

            .chat-input {
                border: 1px solid ${this.theme.primary}40;
                font-family: ${this.theme.fontFamily};
            }

            .chat-input:focus {
                border-color: ${this.theme.primary};
                outline: none;
            }

            .typing-indicator {
                background-color: ${this.theme.background};
            }

            .typing-bubble .dot {
                background-color: ${this.theme.primary}80;
            }

            .status-indicator.online {
                background-color: ${this.theme.success};
            }

            .status-indicator.offline {
                background-color: ${this.theme.error};
            }

            ::-webkit-scrollbar {
                width: 6px;
            }

            ::-webkit-scrollbar-track {
                background: ${this.theme.background};
            }

            ::-webkit-scrollbar-thumb {
                background: ${this.theme.primary}40;
                border-radius: 3px;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: ${this.theme.primary}60;
            }
        `;

        const styleElement = document.createElement('style');
        styleElement.textContent = customStyles;
        document.head.appendChild(styleElement);
    }

    loadEmojiPicker() {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/@joeattardi/emoji-button@latest/dist/index.min.js';
        document.head.appendChild(script);
    }

    loadDraft() {
        this.draftMessage = localStorage.getItem(`chat_draft_${this.customerId}`) || '';
    }

    saveDraft(text) {
        this.draftMessage = text;
        localStorage.setItem(`chat_draft_${this.customerId}`, text);
    }

    createInputArea() {
        const container = document.createElement('div');
        container.style.padding = '10px';
        container.style.borderTop = '1px solid #eee';
        container.style.display = 'flex';
        container.style.alignItems = 'center';
        container.style.gap = '8px';

        const fileInput = this.createFileInput();
        const emojiButton = this.createEmojiButton();
        const textArea = this.createTextArea();
        const sendButton = this.createSendButton();

        container.appendChild(fileInput);
        container.appendChild(emojiButton);
        container.appendChild(textArea);
        container.appendChild(sendButton);

        return container;
    }

    createTextArea() {
        const textArea = document.createElement('textarea');
        textArea.placeholder = 'پیام خود را بنویسید...';
        textArea.value = this.draftMessage;
        textArea.style.flex = '1';
        textArea.style.padding = '8px';
        textArea.style.border = '1px solid #ccc';
        textArea.style.borderRadius = '5px';
        textArea.style.resize = 'none';
        textArea.style.height = '36px';
        textArea.style.maxHeight = '100px';

        textArea.addEventListener('input', (e) => {
            this.saveDraft(e.target.value);
            this.handleTyping();
            this.adjustTextAreaHeight(textArea);
        });

        textArea.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage(textArea.value.trim());
                textArea.value = '';
                this.saveDraft('');
                this.adjustTextAreaHeight(textArea);
            }
        });

        return textArea;
    }


    adjustTextAreaHeight(textArea) {
        textArea.style.height = '36px';
        textArea.style.height = `${textArea.scrollHeight}px`;
    }

    handleTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            this.sendTypingStatus(true);
        }

        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.isTyping = false;
            this.sendTypingStatus(false);
        }, 1000);
    }

    async sendTypingStatus(isTyping) {
        try {
            await fetch(`${this.apiUrl}/typing`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Customer-ID': this.customerId
                },
                body: JSON.stringify({ isTyping })
            });
        } catch (error) {
            console.error('Error sending typing status:', error);
        }
    }

    createFileInput() {
        const container = document.createElement('div');
        container.style.position = 'relative';

        const input = document.createElement('input');
        input.type = 'file';
        input.accept = this.allowedFileTypes.join(',');
        input.style.display = 'none';

        const button = document.createElement('button');
        button.innerHTML = '📎';
        button.style.border = 'none';
        button.style.background = 'none';
        button.style.cursor = 'pointer';
        button.style.fontSize = '20px';
        button.onclick = () => input.click();

        input.addEventListener('change', (e) => this.handleFileUpload(e.target.files[0]));
        container.appendChild(button);
        container.appendChild(input);
        return container;
    }

    async handleFileUpload(file) {
        if (!file) return;

        if (!this.allowedFileTypes.includes(file.type)) {
            this.addMessage('فرمت فایل انتخاب شده پشتیبانی نمی‌شود.', 'error');
            return;
        }

        if (file.size > this.maxFileSize) {
            this.addMessage('حجم فایل بیشتر از حد مجاز است.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.apiUrl}/upload`, {
                method: 'POST',
                headers: {
                    'X-Customer-ID': this.customerId
                },
                body: formData
            });

            const data = await response.json();
            if (data.status === 'success') {
                this.addMessage(`![${file.name}](${data.url})`, 'user');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            this.addMessage('خطا در آپلود فایل', 'error');
        }
    }

    createEmojiButton() {
        const button = document.createElement('button');
        button.innerHTML = '😊';
        button.style.border = 'none';
        button.style.background = 'none';
        button.style.cursor = 'pointer';
        button.style.fontSize = '20px';

        if (window.EmojiButton) {
            const picker = new EmojiButton();
            picker.on('emoji', emoji => {
                const textArea = this.chatWindow.querySelector('textarea');
                textArea.value += emoji;
                this.saveDraft(textArea.value);
            });
            button.onclick = () => picker.togglePicker(button);
        }

        return button;
    }

    createSendButton() {
        const button = document.createElement('button');
        button.innerHTML = '➤';
        button.style.border = 'none';
        button.style.background = '#0084ff';
        button.style.color = 'white';
        button.style.borderRadius = '50%';
        button.style.width = '36px';
        button.style.height = '36px';
        button.style.cursor = 'pointer';
        button.style.display = 'flex';
        button.style.alignItems = 'center';
        button.style.justifyContent = 'center';

        button.onclick = () => {
            const textArea = this.chatWindow.querySelector('textarea');
            if (textArea.value.trim()) {
                this.sendMessage(textArea.value.trim());
                textArea.value = '';
                this.saveDraft('');
                this.adjustTextAreaHeight(textArea);
            }
        };

        return button;
    }

    loadMarkdownParser() {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        script.onload = () => {
            // تنظیمات امنیتی marked
            marked.setOptions({
                sanitize: true,
                breaks: true
            });
        };
        document.head.appendChild(script);
    }

    createTypingIndicator() {
        const typing = document.createElement('div');
        typing.className = 'typing-indicator';
        typing.innerHTML = `
            <div class="typing-bubble">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        return typing;
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            ${this.existingStyles}
            
            .typing-indicator {
                margin: 5px;
                padding: 8px;
                border-radius: 5px;
                background-color: #f5f5f5;
                max-width: 60px;
                align-self: flex-start;
            }
            
            .typing-bubble {
                display: flex;
                gap: 4px;
            }
            
            .typing-bubble .dot {
                width: 6px;
                height: 6px;
                background: #999;
                border-radius: 50%;
                animation: typing-bubble 1s infinite;
            }
            
            .typing-bubble .dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-bubble .dot:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typing-bubble {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-4px); }
            }
            
            .chat-message {
                margin: 5px;
                padding: 8px;
                border-radius: 5px;
                max-width: 80%;
                word-wrap: break-word;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .chat-message pre {
                background: rgba(0,0,0,0.05);
                padding: 8px;
                border-radius: 4px;
                overflow-x: auto;
            }
            
            .chat-message code {
                background: rgba(0,0,0,0.05);
                padding: 2px 4px;
                border-radius: 3px;
                font-family: monospace;
            }
            
            .chat-message a {
                color: #0084ff;
                text-decoration: none;
            }
            
            .chat-message a:hover {
                text-decoration: underline;
            }
        `;
        document.head.appendChild(style);
    }

    setupOnlineStatus() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateStatusIndicator();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateStatusIndicator();
            this.addMessage('اتصال به اینترنت قطع شده است.', 'error');
        });
    }

    createStatusIndicator() {
        const status = document.createElement('div');
        status.style.width = '8px';
        status.style.height = '8px';
        status.style.borderRadius = '50%';
        status.style.marginRight = '8px';
        status.style.backgroundColor = this.isOnline ? '#4caf50' : '#f44336';
        return status;
    }

    updateStatusIndicator() {
        const titleBar = this.chatWindow.querySelector('.chat-title-bar');
        const oldStatus = titleBar.querySelector('.status-indicator');
        if (oldStatus) {
            oldStatus.style.backgroundColor = this.isOnline ? '#4caf50' : '#f44336';
        }
    }

    addMessage(text, type, save = true) {
        const message = document.createElement('div');
        message.className = 'chat-message';

        const timestamp = new Date().toLocaleTimeString();
        const messageContent = document.createElement('div');

        // تبدیل Markdown به HTML اگر marked لود شده باشد
        if (window.marked && type === 'bot') {
            messageContent.innerHTML = marked(text);
        } else {
            messageContent.textContent = text;
        }

        const timeElement = document.createElement('div');
        timeElement.style.fontSize = '10px';
        timeElement.style.color = '#666';
        timeElement.style.marginTop = '4px';
        timeElement.textContent = timestamp;

        if (type === 'user') {
            message.style.marginLeft = 'auto';
            message.style.backgroundColor = '#e3f2fd';
        } else if (type === 'bot') {
            message.style.marginRight = 'auto';
            message.style.backgroundColor = '#f5f5f5';
        } else {
            message.style.marginRight = 'auto';
            message.style.backgroundColor = '#ffebee';
            message.style.color = '#d32f2f';
        }

        message.appendChild(messageContent);
        message.appendChild(timeElement);
        this.messageList.appendChild(message);
        this.messageList.scrollTop = this.messageList.scrollHeight;

        if (save) {
            this.chatHistory.push({
                text,
                type,
                timestamp: new Date().toISOString()
            });
            this.saveChatHistory();
        }
    }

    loadChatHistory() {
        const history = localStorage.getItem(`chat_history_${this.customerId}`);
        this.chatHistory = history ? JSON.parse(history) : [];
    }

    saveChatHistory() {
        localStorage.setItem(
            `chat_history_${this.customerId}`,
            JSON.stringify(this.chatHistory.slice(-20)) // حفظ 20 پیام آخر
        );
    }

    createLoadingIndicator() {
        const loading = document.createElement('div');
        loading.className = 'chat-loading';
        loading.innerHTML = `
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        return loading;
    }

    createTitleBar() {
        const titleBar = document.createElement('div');
        titleBar.className = 'chat-title-bar';
        titleBar.style.padding = '10px';
        titleBar.style.backgroundColor = '#0084ff';
        titleBar.style.color = 'white';
        titleBar.style.borderTopLeftRadius = '10px';
        titleBar.style.borderTopRightRadius = '10px';
        titleBar.style.display = 'flex';
        titleBar.style.justifyContent = 'space-between';
        titleBar.style.alignItems = 'center';

        const leftSection = document.createElement('div');
        leftSection.style.display = 'flex';
        leftSection.style.alignItems = 'center';

        const statusIndicator = this.createStatusIndicator();
        statusIndicator.className = 'status-indicator';

        const titleText = document.createElement('span');
        titleText.textContent = this.title;
        titleText.style.fontWeight = 'bold';

        leftSection.appendChild(statusIndicator);
        leftSection.appendChild(titleText);

        const closeButton = document.createElement('button');
        closeButton.textContent = '✕';
        closeButton.style.background = 'none';
        closeButton.style.border = 'none';
        closeButton.style.color = 'white';
        closeButton.style.cursor = 'pointer';
        closeButton.style.fontSize = '16px';
        closeButton.addEventListener('click', () => this.toggleChat());

        titleBar.appendChild(leftSection);
        titleBar.appendChild(closeButton);
        return titleBar;
    }

    createChatWindow() {
        const div = document.createElement('div');
        div.style.width = '300px';
        div.style.height = '400px';
        div.style.border = '1px solid #ddd';
        div.style.borderRadius = '10px';
        div.style.backgroundColor = 'white';
        div.style.display = 'flex';
        div.style.flexDirection = 'column';
        div.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        return div;
    }

    createToggleButton() {
        const button = document.createElement('button');
        button.innerHTML = `
            <svg viewBox="0 0 24 24" width="24" height="24">
                <path fill="currentColor" d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
            </svg>
        `;
        button.style.width = '50px';
        button.style.height = '50px';
        button.style.borderRadius = '50%';
        button.style.border = 'none';
        button.style.backgroundColor = '#0084ff';
        button.style.color = 'white';
        button.style.cursor = 'pointer';
        button.style.display = 'flex';
        button.style.alignItems = 'center';
        button.style.justifyContent = 'center';
        button.style.marginTop = '10px';
        button.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
        return button;
    }

    toggleChat() {
        this.isOpen = !this.isOpen;
        this.chatWindow.style.display = this.isOpen ? 'flex' : 'none';
    }

    async sendMessage(text) {
        if (!this.isOnline) {
            this.addMessage('لطفاً اتصال اینترنت خود را بررسی کنید.', 'error');
            return;
        }

        this.addMessage(text, 'user');

        // نمایش نشانگر تایپینگ
        const typingIndicator = this.createTypingIndicator();
        this.messageList.appendChild(typingIndicator);

        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Customer-ID': this.customerId
                },
                body: JSON.stringify({
                    text,
                    history: this.chatHistory.slice(-5)
                })
            });

            this.messageList.removeChild(typingIndicator);

            const data = await response.json();
            if (data.status === 'success') {
                this.addMessage(data.message, 'bot');
            }
        } catch (error) {
            this.messageList.removeChild(typingIndicator);
            console.error('Error sending message:', error);
            this.addMessage('متأسفانه مشکلی پیش آمده است.', 'error');
        }
    }

    createContainer() {
        const div = document.createElement('div');
        div.style.position = 'fixed';
        div.style.right = '20px';
        div.style.bottom = '20px';
        div.style.zIndex = '1000';
        return div;
    }

    createMessageList() {
        const div = document.createElement('div');
        div.style.flex = '1';
        div.style.overflow = 'auto';
        div.style.padding = '10px';
        return div;
    }

    createInput() {
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = 'پیام خود را بنویسید...';
        input.style.padding = '10px';
        input.style.margin = '10px';
        input.style.border = '1px solid #ccc';
        input.style.borderRadius = '5px';
        return input;
    }

    addMessage(text, type) {
        const message = document.createElement('div');
        message.style.margin = '5px';
        message.style.padding = '8px';
        message.style.borderRadius = '5px';
        message.style.maxWidth = '80%';
        message.style.wordWrap = 'break-word';

        if (type === 'user') {
            message.style.marginLeft = 'auto';
            message.style.backgroundColor = '#e3f2fd';
        } else {
            message.style.marginRight = 'auto';
            message.style.backgroundColor = '#f5f5f5';
        }

        message.textContent = text;
        this.messageList.appendChild(message);
        this.messageList.scrollTop = this.messageList.scrollHeight;
    }
}

window.ChatWidget = ChatWidget;