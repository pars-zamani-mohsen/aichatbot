import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, IconButton, Paper, Typography, CircularProgress } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { styled } from '@mui/material/styles';

const ChatContainer = styled(Paper)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  padding: theme.spacing(2),
}));

const MessagesContainer = styled(Box)(({ theme }) => ({
  flex: 1,
  overflowY: 'auto',
  marginBottom: theme.spacing(2),
  padding: theme.spacing(1),
}));

const MessageBubble = styled(Box)(({ theme, isUser }) => ({
  maxWidth: '70%',
  padding: theme.spacing(1.5),
  borderRadius: theme.spacing(2),
  marginBottom: theme.spacing(1),
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[100],
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  marginLeft: isUser ? 'auto' : 0,
}));

const SourcesList = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(1),
  padding: theme.spacing(1),
  backgroundColor: theme.palette.grey[50],
  borderRadius: theme.spacing(1),
}));

const ChatWindow = ({ websiteId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [ws, setWs] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // اتصال به WebSocket
    const websocket = new WebSocket(`ws://localhost:8000/api/chats/ws/${websiteId}`);
    
    websocket.onopen = () => {
      console.log('WebSocket Connected');
    };
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.message,
        sources: data.sources
      }]);
      setIsLoading(false);
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setIsLoading(false);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket Disconnected');
    };
    
    setWs(websocket);
    
    return () => {
      websocket.close();
    };
  }, [websiteId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || !ws) return;
    
    // اضافه کردن پیام کاربر به لیست
    setMessages(prev => [...prev, {
      role: 'user',
      content: input
    }]);
    
    // ارسال پیام به سرور
    ws.send(JSON.stringify({
      message: input
    }));
    
    setInput('');
    setIsLoading(true);
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <ChatContainer elevation={3}>
      <MessagesContainer>
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: message.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <MessageBubble isUser={message.role === 'user'}>
              <Typography variant="body1">{message.content}</Typography>
              {message.sources && message.sources.length > 0 && (
                <SourcesList>
                  <Typography variant="caption" color="textSecondary">
                    منابع:
                  </Typography>
                  {message.sources.map((source, idx) => (
                    <Typography
                      key={idx}
                      variant="caption"
                      component="a"
                      href={source}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{ display: 'block', color: 'primary.main' }}
                    >
                      {source}
                    </Typography>
                  ))}
                </SourcesList>
              )}
            </MessageBubble>
          </Box>
        ))}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </MessagesContainer>
      
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="پیام خود را بنویسید..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          multiline
          maxRows={4}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </ChatContainer>
  );
};

export default ChatWindow; 