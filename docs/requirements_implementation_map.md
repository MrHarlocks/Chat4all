# Mapeamento de Requisitos e Implementação

Este documento descreve como cada requisito funcional e não-funcional do projeto **Chat4all** foi atendido pela arquitetura e código atual, detalhando as funções e métodos utilizados.

---

## 2. Requisitos Funcionais

### 2.1 Mensageria Básica

**Requisito:** Criar conversas (1:1 e Grupos), enviar texto e arquivos, recepção em tempo real/offline.

**Implementação:**

- **Modelagem:** O modelo `Conversation` suporta tipos `PRIVATE` e `GROUP`.
- **Fluxo:** A API recebe a mensagem, salva no MongoDB (persistência) e publica no Kafka. Se o usuário estiver offline, a mensagem fica salva no banco e será entregue quando o worker processar a fila.

*Trecho de Código (`src/domain/models.py`):*

```python
class ConversationType(str, Enum):
    PRIVATE = "PRIVATE"
    GROUP = "GROUP"

class Message(BaseModel):
    # Field(default_factory=...): Gera um UUID v4 único automaticamente se não fornecido.
    # Garante que cada mensagem tenha um identificador universal desde a criação.
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    sender_id: UUID
    type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    attachments: List[Attachment] = []
    status: MessageStatus = MessageStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider_metadata: Dict[str, Any] = {}
```

**Alternativas e Justificativa:**
- **Alternativa:** *RabbitMQ* ou *HTTP Polling*.
- **Por que escolhemos Kafka/Mongo:** O RabbitMQ é excelente para filas de tarefas, mas o **Kafka** oferece retenção de mensagens (log) e replayabilidade, crucial para histórico de chat e recuperação de falhas. O **MongoDB** foi escolhido em vez de SQL (PostgreSQL) pela flexibilidade do schema (mensagens de texto, arquivo, localização variam muito) e alta performance de escrita (write-heavy).

### 2.2 Controle de Envio / Entrega / Leitura

**Requisito:** Estados SENT, DELIVERED, READ. Idempotência via `message_id`.

**Implementação:**

- **Estados:** Enum `MessageStatus` rastreia o ciclo de vida.
- **Idempotência:** O `id` é gerado no cliente ou na entrada da API (UUID v4) e usado como chave primária no MongoDB.

*Trecho de Código (`src/domain/models.py` e `src/services/router_service.py`):*

```python
class MessageStatus(str, Enum):
    PENDING = "PENDING"   # Recebido pela API, aguardando processamento
    SENT = "SENT"         # Processado com sucesso pelo Worker/Broker
    DELIVERED = "DELIVERED" # Entregue ao dispositivo (callback)
    READ = "READ"         # Lido pelo usuário (callback)
    FAILED = "FAILED"     # Erro no envio

# Lógica no RouterService:
# provider.send_message(message): Chama o adaptador específico (ex: WhatsApp) para realizar o envio real.
# Retorna True se a plataforma externa aceitou a mensagem.
provider = self.providers.get(target_platform)

if provider:
    success = await provider.send_message(message)
    # Note: Status update to SENT happens here, but DELIVERED/READ comes from callbacks later
    new_status = MessageStatus.SENT if success else MessageStatus.FAILED
    await self.repository.update_status(message.id, new_status)
```

**Alternativas e Justificativa:**
- **Alternativa:** *Auto-increment IDs (Banco de Dados)* e *Polling de Status*.
- **Por que escolhemos UUID v4:** IDs sequenciais vazam informações de volume e exigem round-trip ao banco para serem gerados. **UUIDs** permitem criação offline no cliente e garantem idempotência global. Atualizações atômicas evitam condições de corrida que ocorreriam com transações complexas em bancos SQL.

### 2.3 Multiplataforma e Roteamento

**Requisito:** Escolha de canais, Broker unificador, Mapeamento de usuários.

**Implementação:**

- **Broker:** O `RouterService` atua como o broker central. Ele consome do Kafka e decide qual `Provider` usar.
- **Abstração:** Interface `MessageProvider` permite que diferentes plataformas (WhatsApp, Instagram) sejam tratadas de forma polimórfica.

*Trecho de Código (`src/services/router_service.py`):*

```python
# Dicionário de estratégias (Pattern Strategy):
# Mapeia o enum da plataforma para a instância concreta do adaptador.
self.providers: dict[str, MessageProvider] = {
    Platform.INTERNAL.value: MockProvider(), # Internal/Mock
    Platform.WHATSAPP.value: WhatsAppProvider(),
    Platform.INSTAGRAM.value: InstagramProvider(),
    Platform.TELEGRAM.value: MockProvider(), # Fallback to mock for now
}

# Lógica de Roteamento:
# providers.get(target_platform): Seleciona o adaptador correto em tempo de execução (Polimorfismo).
provider = self.providers.get(target_platform)

if provider:
    # Chama o método padronizado da interface, independente da plataforma subjacente.
    success = await provider.send_message(message)
```

**Alternativas e Justificativa:**
- **Alternativa:** *Blocos If/Else gigantes* ou *Microserviços separados por canal*.
- **Por que escolhemos Strategy Pattern:** *If/Else* torna o código inmanutenível rapidamente. *Microserviços* adicionariam latência de rede e complexidade operacional desnecessária neste estágio. O **Strategy Pattern** permite adicionar novos canais (ex: Telegram) apenas criando uma nova classe, sem tocar no código de roteamento existente (Open/Closed Principle).

### 2.4 Persistência

**Requisito:** Metadados em banco distribuído, arquivos em Object Storage.

**Implementação:**

- **MongoDB:** Armazena conversas e metadados das mensagens.
- **MinIO (S3):** Armazena o binário dos arquivos. O banco guarda apenas o `file_id` e metadados (tamanho, tipo).

*Trecho de Código (`src/adapters/db/message_repository.py`):*

```python
async def create(self, message: Message) -> Message:
    # message.model_dump(mode='json'): Converte o modelo Pydantic para um dicionário Python compatível com BSON.
    db = await get_database()
    message_dict = message.model_dump(mode='json')
    message_dict['_id'] = str(message.id)
    
    # collection.insert_one(...): Método do driver Motor (MongoDB Async).
    # Insere o documento de forma assíncrona, liberando o Event Loop durante a I/O.
    await db[self.collection_name].insert_one(message_dict)
    return message
``` message_dict['_id'] = str(message.id)
    await db[self.collection_name].insert_one(message_dict)
    return message
```

**Alternativas e Justificativa:**
- **Alternativa:** *Armazenar arquivos como BLOBs no Banco* ou *Filesystem local*.
- **Por que escolhemos S3/MinIO:** BLOBs incham o banco de dados, tornando backups lentos e caros. Filesystem local não escala horizontalmente (se a API escalar para 2 máquinas, uma não vê o arquivo da outra). **Object Storage (S3)** é o padrão da indústria para escalabilidade infinita e baixo custo de armazenamento.

### 2.5 API Pública

**Requisito:** API REST para operações.

**Implementação:**

- **Roteamento Modular:** Uso de `APIRouter` para organizar endpoints por domínio.
- **Separação de Responsabilidades:** Cada módulo (`messages`, `files`) tem seu próprio roteador.

*Trecho de Código (`src/api/v1/router.py`):*

```python
# APIRouter(): Classe do FastAPI para agrupar rotas relacionadas.
api_router = APIRouter()

# include_router(...): Monta os sub-roteadores na rota principal.
# prefix="/conversations": Define que todas as rotas desse módulo começarão com esse prefixo.
# tags=["conversations"]: Agrupa as rotas na documentação Swagger UI.
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])

api_router = APIRouter()

api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
```

**Alternativas e Justificativa:**
- **Alternativa:** *Flask* ou *Django*.
- **Por que escolhemos FastAPI:** Flask é síncrono por padrão (bloqueante). Django é robusto mas pesado ("baterias inclusas"). **FastAPI** é nativamente assíncrono (performance próxima a NodeJS/Go), usa **Pydantic** para validação automática (menos código de boilerplate) e gera Swagger automaticamente, acelerando a integração com o Frontend.

### 2.6 Extensibilidade de Canais

**Requisito:** Arquitetura de plugins/adapters.

**Implementação:**

- **Interface Padrão:** `MessageProvider` define o contrato que todos os adaptadores devem seguir.
- **Normalização:** Garante que mensagens de diferentes fontes sejam convertidas para o formato interno.

*Trecho de Código (`src/domain/interfaces/provider.py`):*

```python
class MessageProvider(ABC):
    # @abstractmethod: Decorator que obriga as subclasses a implementarem este método.
    # Garante que todo adaptador saiba enviar mensagens.
    @abstractmethod
    async def send_message(self, message: Message, to_user: User = None) -> bool:
        """Send a message to a user on this platform."""
        pass

    # Contrato para normalização de payload, garantindo uniformidade entre canais.
    @abstractmethod
    async def normalize_payload(self, payload: dict) -> Message:
        """Convert external platform payload to internal Message entity."""
        pass
``` async def send_message(self, message: Message, to_user: User = None) -> bool:
        """Send a message to a user on this platform."""
        pass

    @abstractmethod
    async def normalize_payload(self, payload: dict) -> Message:
        """Convert external platform payload to internal Message entity."""
        pass
```

**Alternativas e Justificativa:**
- **Alternativa:** *Duck Typing* (Python padrão) ou *Herança Concreta*.
- **Por que escolhemos Classes Abstratas (ABC):** Duck typing pode causar erros em tempo de execução se um método faltar. **ABCs** garantem que o contrato seja validado em tempo de inicialização/importação, impedindo que a aplicação suba se um novo adaptador estiver incompleto.

---

## 3. Requisitos Não-Funcionais (NFR)

### 3.1 Escalabilidade

**Requisito:** Capacidade de processar alto volume de mensagens.

**Implementação:**

- **Workers Assíncronos:** Scripts Python rodando em background consumindo do Kafka.
- **Escala Horizontal:** Múltiplos workers podem rodar em paralelo (Consumer Groups).

*Trecho de Código (`src/worker.py`):*

```python
# Este script roda isolado da API e pode ter múltiplas réplicas rodando em paralelo.
async def main():
    # Initialize DB connection
    db_client.connect()
    
    # Initialize Router Service
    service = RouterService()
    
    logger.info(f"Starting Router Worker (PID: {os.getpid()})...")
    try:
        # start_consumer(): Inicia o loop infinito de consumo do Kafka.
        # Ele lê mensagens do tópico 'messages' e as processa uma a uma.
        await service.start_consumer()
```python
async def main():
    # Initialize DB connection
    db_client.connect()
    
    # Initialize Router Service
    service = RouterService()
    
    logger.info(f"Starting Router Worker (PID: {os.getpid()})...")
    try:
        await service.start_consumer()
```

**Alternativas e Justificativa:**
- **Alternativa:** *Celery + Redis* ou *Threads em Background na API*.
- **Por que escolhemos Kafka + Workers:** Threads na API consomem CPU do servidor web e morrem se a API reiniciar. Celery é ótimo para tarefas, mas o **Kafka** permite processamento de stream real, replay de eventos passados e desacoplamento total. Workers independentes permitem escalar o processamento (CPU-bound) separadamente da API (IO-bound).

### 3.2 Alta Disponibilidade / Tolerância a Falhas

**Requisito:** Failover automático, detecção de falhas.

**Implementação:**

- **Infraestrutura:** Docker Compose com serviços resilientes (Kafka, Mongo).
- **Recuperação:** Testes demonstraram (`scripts/fault_tolerance_test.py`) que se um worker cai, o grupo de consumidores do Kafka rebalanceia e outros workers assumem a carga.

**Alternativas e Justificativa:**
- **Alternativa:** *Kubernetes (K8s)* ou *Cluster de VMs*.
- **Por que escolhemos Docker Compose + Consumer Groups:** K8s adicionaria complexidade operacional imensa para o estágio atual. O mecanismo nativo de **Consumer Groups do Kafka** já oferece failover automático de processamento sem precisar de orquestradores complexos.

### 3.3 Consistência & Garantias

**Requisito:** At-least-once, Ordem causal.

**Implementação:**

- **Kafka:** Garante a ordem dentro da partição.
- **MongoDB:** Garante a persistência atômica do documento da mensagem antes do envio para a fila.

**Alternativas e Justificativa:**
- **Alternativa:** *Two-Phase Commit (2PC)* ou *Transações Distribuídas*.
- **Por que escolhemos Consistência Eventual:** 2PC é lento e bloqueante, matando a performance. A combinação de **Ordem por Partição (Kafka)** e **Atomicidade de Documento (Mongo)** é suficiente para garantir a ordem causal de um chat (quem falou o que e quando) com performance muito superior.

### 3.4 Latência

**Requisito:** <200ms para caminhos internos.

**Implementação:**

- **Assincronismo:** Uso de `asyncio` e `Motor` (driver Mongo async) em toda a stack para não bloquear I/O.
- **Métricas:** Monitoramento via Prometheus mostra latência média de processamento na casa dos milissegundos (verificado nos dashboards).

**Alternativas e Justificativa:**
- **Alternativa:** *Threading* ou *Drivers Síncronos (PyMongo)*.
- **Por que escolhemos Asyncio:** Threads têm overhead de memória e troca de contexto. **Asyncio** permite lidar com milhares de conexões simultâneas (WebSocket/HTTP) em uma única thread, ideal para I/O bound como chat.

### 3.5 Throughput

**Requisito:** Milhares de mensagens/s.

**Implementação:**

- **Batching:** Kafka suporta envio e consumo em lote.
- **Particionamento:** O tópico `messages` foi configurado com 4 partições (`scripts/setup_kafka.py`) para permitir paralelismo de até 4 workers simultâneos.

**Alternativas e Justificativa:**
- **Alternativa:** *Processamento Serial* ou *Webhooks HTTP diretos*.
- **Por que escolhemos Batching + Particionamento:** Webhooks diretos podem derrubar o recebedor em picos de tráfego (DDoS acidental). O **Kafka** age como um buffer (backpressure), e o particionamento permite paralelizar o trabalho infinitamente apenas adicionando mais workers.

### 3.6 Armazenamento de Arquivos

**Requisito:** Uploads até 2GB, Chunked/S3.

**Implementação:**

- **Presigned URLs:** A API não recebe o arquivo diretamente (o que bloquearia a thread). Ela gera uma URL assinada do MinIO (S3) para o cliente fazer o upload direto.

*Trecho de Código (`src/services/file_service.py`):*

```python
    async def generate_upload_url(
        self, 
        filename: str, 
        mime_type: str, 
        size: int, 
        uploader_id: UUID, 
        conversation_id: Optional[UUID] = None,
        checksum: Optional[str] = None
    ):
        file_id = uuid4()
        extension = filename.split('.')[-1] if '.' in filename else 'bin'
        object_name = f"{file_id}.{extension}"
        
        # Note: generate_presigned_url is synchronous in boto3, but we wrap it in async service method
        # for consistency and potential future async implementation
        # generate_presigned_url(...): Método do Boto3 (AWS SDK).
        # Cria uma URL temporária e segura que permite ao frontend fazer PUT direto no Bucket S3.
        upload_url = self.s3.generate_presigned_url(object_name, method='put_object')
        
        # Construct a public URL (assuming bucket policy allows read or using MinIO browser)
        # In production, this might be a CloudFront URL
        public_url = f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET_NAME}/{object_name}"

        # Save metadata
        file_metadata = FileMetadata(
            id=file_id,
            filename=filename,
            mime_type=mime_type,
            size=size,
            uploader_id=uploader_id,
            conversation_id=conversation_id,
            checksum=checksum
        )
        await self.file_metadata_repo.create(file_metadata)

        return upload_url, public_url
```

**Alternativas e Justificativa:**
- **Alternativa:** *Upload via API (Proxy)*.
- **Por que escolhemos Presigned URLs:** Fazer upload via API consome memória e threads do servidor de aplicação enquanto o arquivo trafega. **Presigned URLs** permitem que o cliente fale direto com o Storage (S3), liberando a API para processar apenas metadados leves.

### 3.7 Operacional / Observabilidade

**Requisito:** Monitoramento, Tracing, Logs.

**Implementação:**

- **Middleware:** `MetricsMiddleware` intercepta todas as requisições para coletar latência e contagem.
- **Prometheus/Grafana:** Stack configurada no `docker-compose.yml` para visualização.

*Trecho de Código (`src/core/metrics.py`):*

```python
# Counter: Métrica cumulativa que só aumenta (ex: total de requisições).
# Usado para contar eventos discretos, como mensagens processadas.
MESSAGES_PROCESSED_TOTAL = Counter(
    'messages_processed_total', 
    'Total number of messages processed',
    ['status', 'type']
)

# Histogram: Agrupa observações (como latência) em buckets para calcular percentis (P95, P99).
# Essencial para entender a performance e distribuição do tempo de resposta.
MESSAGE_LATENCY_SECONDS = Histogram(
    'message_latency_seconds',
    'Time spent processing messages',
    ['operation']
)

# Middleware: Intercepta todas as requisições HTTP.
# Permite coletar métricas de forma transparente sem poluir a lógica de negócio.
class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Gauge: Métrica que pode subir e descer.
        # Útil para monitorar estado atual, como conexões ativas.
        ACTIVE_CONNECTIONS.inc()
        start_time = time.time()
        
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            ERRORS_TOTAL.labels(type=type(e).__name__).inc()
            raise e
        finally:
            ACTIVE_CONNECTIONS.dec()
            duration = time.time() - start_time
            # observe(duration): Registra o tempo que a requisição levou no histograma.
            MESSAGE_LATENCY_SECONDS.labels(operation=scope['path']).observe(duration)
```

**Alternativas e Justificativa:**
- **Alternativa:** *ELK Stack (Elasticsearch)* ou *SaaS (Datadog, New Relic)*.
- **Por que escolhemos Prometheus/Grafana:** ELK é focado em logs e muito pesado. SaaS é caro. **Prometheus** é o padrão cloud-native para métricas (time-series), leve e open-source, integrando perfeitamente com Kubernetes no futuro.

### 3.8 Documentação e Arquitetura

**Requisito:** Documentação automática e código desacoplado.

**Implementação:**

- **OpenAPI:** O FastAPI gera automaticamente a documentação em `/docs`.
- **Arquitetura Hexagonal (Adapters):** O código é organizado em `domain`, `services` e `adapters`, facilitando a manutenção.

*Trecho de Código (`src/main.py`):*

```python
# FastAPI(...): Inicializa a aplicação.
# Os parâmetros title e description são usados para gerar a página HTML do Swagger UI.
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    API do Roteador Universal de Mensagens
    
    Funcionalidades:
    - Envio e recebimento de mensagens entre plataformas (Interno, WhatsApp, Telegram, etc.)
    - Suporte a transferência de arquivos grandes (até 2GB)
    - Gerenciamento de conversas em grupo
    - Rastreamento de status de mensagens
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Metrics Endpoint: Exposição de métricas para o Prometheus.
# O Prometheus faz scraping neste endpoint periodicamente.
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middlewares: Camadas que processam requisições antes de chegar nas rotas.
# LoggingMiddleware: Loga detalhes de cada requisição.
# MetricsMiddleware: Coleta métricas de tempo e contagem.
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# Exception Handlers: Tratamento global de erros.
# Garante que erros não tratados retornem respostas JSON padronizadas.
add_exception_handlers(app)

# Include Router: Registra as rotas da API (v1).
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health.router, tags=["health"])
```

**Alternativas e Justificativa:**
- **Alternativa:** *MVC (Model-View-Controller)* ou *Monólito em Camadas*.
- **Por que escolhemos Arquitetura Hexagonal (Ports & Adapters):** MVC acopla a lógica de negócio ao framework web. A **Arquitetura Hexagonal** isola o `domain` (regras de negócio) de detalhes externos como Banco de Dados ou API. Isso permite testar a lógica de negócio sem subir o banco e trocar o Kafka por RabbitMQ (ou vice-versa) mexendo apenas nos adaptadores, sem risco de quebrar a regra de negócio.
