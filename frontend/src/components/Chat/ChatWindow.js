import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { chats } from '../../services/api';

const ChatWindow = ({ websiteId }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadChatHistory = async () => {
      try {
        // ابتدا چت‌های وب‌سایت را دریافت می‌کنیم
        const websiteChats = await chats.getWebsiteChats(websiteId);
        console.log('Website chats:', websiteChats);
        
        if (websiteChats && websiteChats.length > 0) {
          // از آخرین چت استفاده می‌کنیم
          const lastChat = websiteChats[websiteChats.length - 1];
          console.log('Using chat:', lastChat);
          
          // دریافت پیام‌های چت
          const history = await chats.getHistory(lastChat.id);
          console.log('Chat history:', history);
          
          if (history && history.length > 0) {
            const formattedMessages = history.map(msg => ({
              role: msg.role,
              content: msg.content,
              timestamp: msg.created_at
            }));
            setMessages(formattedMessages);
          }
        }
      } catch (err) {
        console.error('Error loading chat history:', err);
        setError('خطا در بارگذاری سابقه چت');
      }
    };

    if (websiteId) {
      loadChatHistory();
    }
  }, [websiteId]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: newMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setLoading(true);
    setError('');

    try {
      const response = await chats.create(websiteId, newMessage);
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError('خطا در ارسال پیام');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">چت</Typography>
      </Box>

      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <List>
          {messages.map((message, index) => (
            <React.Fragment key={index}>
              <ListItem
                sx={{
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <Paper
                  sx={{
                    p: 2,
                    maxWidth: '70%',
                    bgcolor: message.role === 'user' ? 'primary.main' : 'grey.100',
                    color: message.role === 'user' ? 'white' : 'text.primary'
                  }}
                >
                  <Typography variant="body1">{message.content}</Typography>
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </Typography>
                </Paper>
              </ListItem>
              {index < messages.length - 1 && <Divider />}
            </React.Fragment>
          ))}
          <div ref={messagesEndRef} />
        </List>
      </Box>

      {error && (
        <Typography color="error" sx={{ p: 2 }}>
          {error}
        </Typography>
      )}

      <Box
        component="form"
        onSubmit={handleSend}
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          display: 'flex',
          gap: 1
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="پیام خود را بنویسید..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          disabled={loading}
          dir="rtl"
        />
        <IconButton
          color="primary"
          type="submit"
          disabled={loading || !newMessage.trim()}
        >
          {loading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </Box>
    </Box>
  );
};

export default ChatWindow; 