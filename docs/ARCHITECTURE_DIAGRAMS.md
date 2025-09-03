# نمودارهای معماری - سیستم چت‌بات هوشمند

## فهرست مطالب
- [معماری کلی سیستم](#معماری-کلی-سیستم)
- [جریان داده](#جریان-داده)
- [معماری احراز هویت](#معماری-احراز-هویت)
- [معماری چت و RAG](#معماری-چت-و-rag)
- [معماری کراولینگ](#معماری-کراولینگ)
- [معماری دیتابیس](#معماری-دیتابیس)

## معماری کلی سیستم

### نمودار لایه‌ای سیستم

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React UI]
        Widget[Widget Embed]
    end
    
    subgraph "API Gateway Layer"
        API[FastAPI Gateway]
        Auth[Authentication]
        RateLimit[Rate Limiting]
        CORS[CORS Middleware]
    end
    
    subgraph "Business Logic Layer"
        ChatService[Chat Service]
        WebsiteService[Website Service]
        CrawlService[Crawl Service]
        UserService[User Service]
        AdminService[Admin Service]
    end
    
    subgraph "AI & ML Layer"
        RAGService[RAG Service]
        EmbeddingService[Embedding Service]
        ChatbotManager[Chatbot Manager]
        AIModels[AI Models]
    end
    
    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL)]
        ChromaDB[(ChromaDB)]
        Redis[(Redis Cache)]
        FileStorage[File Storage]
    end
    
    UI --> API
    Widget --> API
    API --> Auth
    Auth --> RateLimit
    RateLimit --> CORS
    CORS --> ChatService
    CORS --> WebsiteService
    CORS --> CrawlService
    CORS --> UserService
    CORS --> AdminService
    
    ChatService --> RAGService
    WebsiteService --> CrawlService
    CrawlService --> EmbeddingService
    RAGService --> ChatbotManager
    ChatbotManager --> AIModels
    
    ChatService --> PostgreSQL
    WebsiteService --> PostgreSQL
    UserService --> PostgreSQL
    AdminService --> PostgreSQL
    RAGService --> ChromaDB
    EmbeddingService --> ChromaDB
    ChatService --> Redis
    RateLimit --> Redis
```

## جریان داده

### نمودار جریان درخواست چت

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI
    participant Auth as Auth Service
    participant Chat as Chat Service
    participant RAG as RAG Service
    participant AI as AI Model
    participant DB as Database
    participant CDB as ChromaDB
    
    U->>F: ارسال سوال
    F->>API: POST /api/chats/
    API->>Auth: بررسی توکن
    Auth-->>API: تأیید کاربر
    
    API->>Chat: پردازش درخواست چت
    Chat->>DB: دریافت اطلاعات وب‌سایت
    DB-->>Chat: اطلاعات وب‌سایت
    
    Chat->>RAG: درخواست جستجو
    RAG->>CDB: جستجو در پایگاه دانش
    CDB-->>RAG: نتایج مرتبط
    
    RAG->>AI: ارسال سوال + context
    AI-->>RAG: پاسخ تولید شده
    
    RAG-->>Chat: پاسخ نهایی
    Chat->>DB: ذخیره چت و پیام
    DB-->>Chat: تأیید ذخیره
    
    Chat-->>API: پاسخ چت
    API-->>F: پاسخ JSON
    F-->>U: نمایش پاسخ
```

### نمودار جریان کراولینگ وب‌سایت

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI
    participant WS as Website Service
    participant CS as Crawl Service
    participant ES as Embedding Service
    participant CDB as ChromaDB
    participant DB as Database
    
    U->>F: درخواست کراولینگ
    F->>API: POST /api/websites/{id}/crawl
    API->>WS: شروع کراولینگ
    
    WS->>CS: شروع کراولر
    CS->>CS: کراول صفحات
    CS-->>WS: صفحات کراول شده
    
    WS->>ES: پردازش embeddings
    ES->>ES: ایجاد embeddings
    ES-->>WS: embeddings آماده
    
    WS->>CDB: ذخیره در ChromaDB
    CDB-->>WS: تأیید ذخیره
    
    WS->>DB: به‌روزرسانی وضعیت
    DB-->>WS: تأیید به‌روزرسانی
    
    WS-->>API: تکمیل کراولینگ
    API-->>F: پاسخ موفقیت
    F-->>U: نمایش وضعیت
```

## معماری احراز هویت

### نمودار جریان احراز هویت

```mermaid
graph LR
    subgraph "Client"
        Login[Login Form]
        Token[Token Storage]
    end
    
    subgraph "API Gateway"
        AuthEndpoint[/auth/login]
        JWTValidation[JWT Validation]
    end
    
    subgraph "Auth Service"
        PasswordCheck[Password Check]
        JWTGenerator[JWT Generator]
        UserDB[User Database]
    end
    
    subgraph "Security"
        RateLimit[Rate Limiting]
        CORS[CORS Policy]
        Headers[Security Headers]
    end
    
    Login --> AuthEndpoint
    AuthEndpoint --> PasswordCheck
    PasswordCheck --> UserDB
    UserDB --> JWTGenerator
    JWTGenerator --> Token
    
    Token --> JWTValidation
    JWTValidation --> RateLimit
    RateLimit --> CORS
    CORS --> Headers
```

## معماری چت و RAG

### نمودار معماری RAG

```mermaid
graph TB
    subgraph "Input Layer"
        UserQuery[User Query]
        ChatHistory[Chat History]
    end
    
    subgraph "Retrieval Layer"
        QueryProcessor[Query Processor]
        HybridSearch[Hybrid Search]
        BM25[BM25 Search]
        VectorSearch[Vector Search]
    end
    
    subgraph "Knowledge Base"
        ChromaDB[(ChromaDB)]
        Documents[Documents]
        Embeddings[Embeddings]
        Metadata[Metadata]
    end
    
    subgraph "Generation Layer"
        ContextBuilder[Context Builder]
        PromptManager[Prompt Manager]
        AIInterface[AI Model Interface]
    end
    
    subgraph "AI Models"
        OpenAI[OpenAI GPT]
        Gemini[Google Gemini]
        Ollama[Ollama Local]
    end
    
    subgraph "Output Layer"
        ResponseGenerator[Response Generator]
        QualityCheck[Quality Check]
        FinalResponse[Final Response]
    end
    
    UserQuery --> QueryProcessor
    ChatHistory --> QueryProcessor
    
    QueryProcessor --> HybridSearch
    HybridSearch --> BM25
    HybridSearch --> VectorSearch
    
    BM25 --> ChromaDB
    VectorSearch --> ChromaDB
    ChromaDB --> Documents
    ChromaDB --> Embeddings
    ChromaDB --> Metadata
    
    Documents --> ContextBuilder
    Embeddings --> ContextBuilder
    Metadata --> ContextBuilder
    
    ContextBuilder --> PromptManager
    PromptManager --> AIInterface
    
    AIInterface --> OpenAI
    AIInterface --> Gemini
    AIInterface --> Ollama
    
    OpenAI --> ResponseGenerator
    Gemini --> ResponseGenerator
    Ollama --> ResponseGenerator
    
    ResponseGenerator --> QualityCheck
    QualityCheck --> FinalResponse
```

## معماری کراولینگ

### نمودار معماری کراولر

```mermaid
graph TB
    subgraph "Crawler Pipeline"
        URLQueue[URL Queue]
        PageFetcher[Page Fetcher]
        ContentParser[Content Parser]
        LinkExtractor[Link Extractor]
        DuplicateFilter[Duplicate Filter]
    end
    
    subgraph "Content Processing"
        TextExtractor[Text Extractor]
        HTMLCleaner[HTML Cleaner]
        LanguageDetector[Language Detector]
        ContentValidator[Content Validator]
    end
    
    subgraph "Storage"
        RawData[Raw Data]
        ProcessedData[Processed Data]
        FileSystem[File System]
    end
    
    subgraph "Embedding Pipeline"
        TextChunker[Text Chunker]
        EmbeddingGenerator[Embedding Generator]
        VectorStore[Vector Store]
    end
    
    URLQueue --> PageFetcher
    PageFetcher --> ContentParser
    ContentParser --> LinkExtractor
    LinkExtractor --> DuplicateFilter
    DuplicateFilter --> URLQueue
    
    ContentParser --> TextExtractor
    TextExtractor --> HTMLCleaner
    HTMLCleaner --> LanguageDetector
    LanguageDetector --> ContentValidator
    
    ContentValidator --> RawData
    RawData --> ProcessedData
    ProcessedData --> FileSystem
    
    ProcessedData --> TextChunker
    TextChunker --> EmbeddingGenerator
    EmbeddingGenerator --> VectorStore
```

## معماری دیتابیس

### نمودار ERD (Entity Relationship Diagram)

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string full_name
        string hashed_password
        string role
        boolean is_active
        datetime created_at
        datetime last_login
        int login_attempts
        datetime locked_until
    }
    
    WEBSITES {
        int id PK
        string url UK
        string name
        string description
        string status
        int owner_id FK
        string collection_name
        json crawl_info
        datetime created_at
        datetime updated_at
    }
    
    CHATS {
        int id PK
        int website_id FK
        string session_id
        datetime created_at
        datetime updated_at
    }
    
    MESSAGES {
        int id PK
        int chat_id FK
        string role
        text content
        datetime created_at
        json metadata
    }
    
    USER_SETTINGS {
        int id PK
        int user_id FK
        json preferences
        string timezone
        boolean email_notifications
        datetime created_at
        datetime updated_at
    }
    
    SYSTEM_SETTINGS {
        int id PK
        string key UK
        string value
        string value_type
        string description
        datetime created_at
        datetime updated_at
    }
    
    USERS ||--o{ WEBSITES : owns
    USERS ||--o{ USER_SETTINGS : has
    WEBSITES ||--o{ CHATS : contains
    CHATS ||--o{ MESSAGES : has
    SYSTEM_SETTINGS ||--o{ } : configures
```

### نمودار معماری دیتابیس

```mermaid
graph TB
    subgraph "Application Layer"
        FastAPI[FastAPI App]
        ORM[SQLAlchemy ORM]
    end
    
    subgraph "Database Layer"
        PostgreSQL[(PostgreSQL)]
        ChromaDB[(ChromaDB)]
        Redis[(Redis)]
    end
    
    subgraph "Data Models"
        UserModel[User Model]
        WebsiteModel[Website Model]
        ChatModel[Chat Model]
        MessageModel[Message Model]
    end
    
    subgraph "Vector Database"
        Collections[Collections]
        Embeddings[Embeddings]
        Documents[Documents]
        Metadata[Metadata]
    end
    
    subgraph "Cache Layer"
        SessionCache[Session Cache]
        RateLimitCache[Rate Limit Cache]
        QueryCache[Query Cache]
    end
    
    FastAPI --> ORM
    ORM --> UserModel
    ORM --> WebsiteModel
    ORM --> ChatModel
    ORM --> MessageModel
    
    UserModel --> PostgreSQL
    WebsiteModel --> PostgreSQL
    ChatModel --> PostgreSQL
    MessageModel --> PostgreSQL
    
    FastAPI --> Collections
    Collections --> Embeddings
    Collections --> Documents
    Collections --> Metadata
    
    FastAPI --> SessionCache
    FastAPI --> RateLimitCache
    FastAPI --> QueryCache
    
    SessionCache --> Redis
    RateLimitCache --> Redis
    QueryCache --> Redis
```

## نمودار Deployment

### نمودار معماری Deployment

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        Mobile[Mobile App]
        Widget[Embedded Widget]
    end
    
    subgraph "Load Balancer"
        Nginx[Nginx Load Balancer]
        SSL[SSL Termination]
    end
    
    subgraph "Application Layer"
        Backend1[Backend Instance 1]
        Backend2[Backend Instance 2]
        Backend3[Backend Instance 3]
    end
    
    subgraph "Database Layer"
        PostgreSQL[(PostgreSQL Primary)]
        PostgreSQLReplica[(PostgreSQL Replica)]
        ChromaDB[(ChromaDB)]
        Redis[(Redis Cluster)]
    end
    
    subgraph "Storage Layer"
        FileStorage[File Storage]
        BackupStorage[Backup Storage]
    end
    
    subgraph "Monitoring"
        Prometheus[Prometheus]
        Grafana[Grafana]
        Logs[Log Aggregation]
    end
    
    Browser --> Nginx
    Mobile --> Nginx
    Widget --> Nginx
    
    Nginx --> SSL
    SSL --> Backend1
    SSL --> Backend2
    SSL --> Backend3
    
    Backend1 --> PostgreSQL
    Backend2 --> PostgreSQL
    Backend3 --> PostgreSQL
    
    Backend1 --> ChromaDB
    Backend2 --> ChromaDB
    Backend3 --> ChromaDB
    
    Backend1 --> Redis
    Backend2 --> Redis
    Backend3 --> Redis
    
    PostgreSQL --> PostgreSQLReplica
    PostgreSQL --> FileStorage
    FileStorage --> BackupStorage
    
    Backend1 --> Prometheus
    Backend2 --> Prometheus
    Backend3 --> Prometheus
    
    Prometheus --> Grafana
    Prometheus --> Logs
```

## نمودار Security

### نمودار معماری امنیت

```mermaid
graph TB
    subgraph "External Threats"
        DDoS[DDoS Attacks]
        SQLInjection[SQL Injection]
        XSS[XSS Attacks]
        CSRF[CSRF Attacks]
    end
    
    subgraph "Security Layers"
        WAF[Web Application Firewall]
        RateLimit[Rate Limiting]
        InputValidation[Input Validation]
        CORS[CORS Policy]
    end
    
    subgraph "Authentication"
        JWT[JWT Tokens]
        PasswordHash[Password Hashing]
        TwoFactor[2FA Support]
        SessionMgmt[Session Management]
    end
    
    subgraph "Data Protection"
        Encryption[Data Encryption]
        HTTPS[HTTPS/TLS]
        Headers[Security Headers]
        Logging[Audit Logging]
    end
    
    DDoS --> WAF
    SQLInjection --> InputValidation
    XSS --> InputValidation
    CSRF --> CORS
    
    WAF --> RateLimit
    RateLimit --> InputValidation
    InputValidation --> CORS
    
    CORS --> JWT
    JWT --> PasswordHash
    PasswordHash --> TwoFactor
    TwoFactor --> SessionMgmt
    
    SessionMgmt --> Encryption
    Encryption --> HTTPS
    HTTPS --> Headers
    Headers --> Logging
```

## نمودار Performance

### نمودار معماری Performance

```mermaid
graph TB
    subgraph "Client Side"
        BrowserCache[Browser Cache]
        CDN[CDN]
    end
    
    subgraph "Application Layer"
        ConnectionPool[Connection Pooling]
        AsyncProcessing[Async Processing]
        BackgroundTasks[Background Tasks]
    end
    
    subgraph "Caching Layer"
        RedisCache[Redis Cache]
        MemoryCache[Memory Cache]
        QueryCache[Query Cache]
    end
    
    subgraph "Database Layer"
        ReadReplicas[Read Replicas]
        ConnectionPooling[DB Connection Pooling]
        QueryOptimization[Query Optimization]
    end
    
    subgraph "Monitoring"
        Metrics[Performance Metrics]
        Profiling[Code Profiling]
        Alerting[Performance Alerting]
    end
    
    BrowserCache --> CDN
    CDN --> ConnectionPool
    
    ConnectionPool --> AsyncProcessing
    AsyncProcessing --> BackgroundTasks
    
    BackgroundTasks --> RedisCache
    BackgroundTasks --> MemoryCache
    BackgroundTasks --> QueryCache
    
    RedisCache --> ReadReplicas
    MemoryCache --> ConnectionPooling
    QueryCache --> QueryOptimization
    
    ReadReplicas --> Metrics
    ConnectionPooling --> Profiling
    QueryOptimization --> Alerting
```

## نکات مهم نمودارها

### 1. **معماری کلی**
- سیستم از معماری لایه‌ای استفاده می‌کند
- هر لایه مسئولیت مشخصی دارد
- ارتباط بین لایه‌ها از طریق API انجام می‌شود

### 2. **جریان داده**
- تمام درخواست‌ها از طریق API Gateway عبور می‌کنند
- احراز هویت در لایه API انجام می‌شود
- داده‌ها در لایه‌های مختلف پردازش می‌شوند

### 3. **امنیت**
- چندین لایه امنیتی پیاده‌سازی شده
- Rate limiting و CORS محافظت می‌کنند
- JWT برای احراز هویت استفاده می‌شود

### 4. **Performance**
- Caching در چندین لایه پیاده‌سازی شده
- Connection pooling برای دیتابیس
- Async processing برای عملیات سنگین

### 5. **Monitoring**
- سیستم‌های monitoring در تمام لایه‌ها
- Logging و metrics برای debugging
- Alerting برای مشکلات عملکرد
