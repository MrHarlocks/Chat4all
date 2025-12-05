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
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    conversation_id: str
    type: MessageType  # Enum que define se o payload é TEXT ou FILE
    content: Optional[str]
    file_id: Optional[str]
    # ...
```

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
success = await provider.send_message(message)

# Define o novo status com base no sucesso do envio
new_status = MessageStatus.SENT if success else MessageStatus.FAILED

# repository.update_status(...): Atualiza atomicamente o campo 'status' no documento do MongoDB
await self.repository.update_status(message.id, new_status)
```

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
    Platform.INTERNAL.value: MockProvider(),       # Simula envio interno
    Platform.WHATSAPP.value: WhatsAppProvider(),   # Adaptador Meta API
    Platform.INSTAGRAM.value: InstagramProvider(), # Adaptador Instagram Graph API
}

# Lógica de Roteamento:
# providers.get(target_platform): Seleciona o adaptador correto em tempo de execução (Polimorfismo).
provider = self.providers.get(target_platform)

if provider:
    # Chama o método padronizado da interface, independente da plataforma subjacente.
    await provider.send_message(message)
```

### 2.4 Persistência

**Requisito:** Metadados em banco distribuído, arquivos em Object Storage.

**Implementação:**

- **MongoDB:** Armazena conversas e metadados das mensagens.
- **MinIO (S3):** Armazena o binário dos arquivos. O banco guarda apenas o `file_id` e metadados (tamanho, tipo).

*Trecho de Código (`src/adapters/db/message_repository.py`):*

```python
async def create(self, message: Message) -> Message:
    # message.dict(): Converte o modelo Pydantic para um dicionário Python compatível com BSON.
    message_dict = message.dict()
    
    # collection.insert_one(...): Método do driver Motor (MongoDB Async).
    # Insere o documento de forma assíncrona, liberando o Event Loop durante a I/O.
    await self.collection.insert_one(message_dict)
    return message
```

### 2.5 API Pública

**Requisito:** API REST para operações.

**Implementação:**

- **FastAPI:** Framework utilizado para expor endpoints RESTful.
- **Endpoints:** `/conversations`, `/messages`, `/files`.

*Trecho de Código (`src/api/v1/router.py`):*

```python
# APIRouter(): Classe do FastAPI para agrupar rotas relacionadas.
api_router = APIRouter()

# include_router(...): Monta os sub-roteadores na rota principal.
# prefix="/conversations": Define que todas as rotas desse módulo começarão com esse prefixo.
# tags=["conversations"]: Agrupa as rotas na documentação Swagger UI.
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
```

### 2.6 Extensibilidade de Canais

**Requisito:** Arquitetura de plugins/adapters.

**Implementação:**

- **Interface:** A classe abstrata `MessageProvider` define o contrato que qualquer novo canal deve seguir.

*Trecho de Código (`src/domain/interfaces/provider.py`):*

```python
class MessageProvider(ABC):
    # @abstractmethod: Decorator que obriga as subclasses a implementarem este método.
    # Garante que todo adaptador saiba enviar mensagens.
    @abstractmethod
    async def send_message(self, message: Message) -> bool:
        pass

    # Contrato para envio de arquivos, garantindo uniformidade entre canais.
    @abstractmethod
    async def send_file(self, message: Message, file_url: str) -> bool:
        pass
```

---

## 3. Requisitos Não-Funcionais (NFR)

### 3.1 Escalabilidade

**Requisito:** Suportar alto tráfego, arquitetura stateless, auto-scale.

**Implementação:**

- **Desacoplamento:** Uso de **Apache Kafka** para desacoplar a recepção (API) do processamento (Workers).
- **Workers Independentes:** O script `src/worker.py` pode ser instanciado N vezes (escalabilidade horizontal) para aumentar o throughput de consumo.

*Trecho de Código (`src/worker.py`):*

```python
# Este script roda isolado da API e pode ter múltiplas réplicas rodando em paralelo.
async def main():
    service = RouterService()
    
    # start_consumer(): Inicia o loop infinito de consumo do Kafka.
    # Ele lê mensagens do tópico 'messages' e as processa uma a uma.
    await service.start_consumer() 
```

### 3.2 Alta Disponibilidade / Tolerância a Falhas

**Requisito:** Failover automático, detecção de falhas.

**Implementação:**

- **Infraestrutura:** Docker Compose com serviços resilientes (Kafka, Mongo).
- **Recuperação:** Testes demonstraram (`scripts/fault_tolerance_test.py`) que se um worker cai, o grupo de consumidores do Kafka rebalanceia e outros workers assumem a carga.

### 3.3 Consistência & Garantias

**Requisito:** At-least-once, Ordem causal.

**Implementação:**

- **Kafka:** Garante a ordem dentro da partição.
- **MongoDB:** Garante a persistência atômica do documento da mensagem antes do envio para a fila.

### 3.4 Latência

**Requisito:** <200ms para caminhos internos.

**Implementação:**

- **Assincronismo:** Uso de `asyncio` e `Motor` (driver Mongo async) em toda a stack para não bloquear I/O.
- **Métricas:** Monitoramento via Prometheus mostra latência média de processamento na casa dos milissegundos (verificado nos dashboards).

### 3.5 Throughput

**Requisito:** Milhares de mensagens/s.

**Implementação:**

- **Batching:** Kafka suporta envio e consumo em lote.
- **Particionamento:** O tópico `messages` foi configurado com 4 partições (`scripts/setup_kafka.py`) para permitir paralelismo de até 4 workers simultâneos.

### 3.6 Armazenamento de Arquivos

**Requisito:** Uploads até 2GB, Chunked/S3.

**Implementação:**

- **Presigned URLs:** A API não recebe o arquivo diretamente (o que bloquearia a thread). Ela gera uma URL assinada do MinIO (S3) para o cliente fazer o upload direto.

*Trecho de Código (`src/services/file_service.py`):*

```python
def generate_upload_url(self, filename: str) -> dict:
    # generate_presigned_url(...): Método do Boto3 (AWS SDK).
    # Cria uma URL temporária e segura que permite ao frontend fazer PUT direto no Bucket S3.
    # 'ExpiresIn=3600': A URL expira em 1 hora.
    url = self.s3_client.generate_presigned_url(
        'put_object',
        Params={'Bucket': settings.MINIO_BUCKET, 'Key': object_name},
        ExpiresIn=3600
    )
    return {"upload_url": url, "file_id": object_name}
```

### 3.7 Operacional / Observabilidade

**Requisito:** Monitoramento, Tracing, Logs.

**Implementação:**

- **Middleware:** `MetricsMiddleware` intercepta todas as requisições para coletar latência e contagem.
- **Prometheus/Grafana:** Stack configurada no `docker-compose.yml` para visualização.

*Trecho de Código (`src/core/metrics.py`):*

```python
# Counter: Métrica cumulativa que só aumenta (ex: total de requisições).
MESSAGES_PROCESSED_TOTAL = Counter('messages_processed_total', ...)

# Histogram: Agrupa observações (como latência) em buckets para calcular percentis (P95, P99).
MESSAGE_LATENCY_SECONDS = Histogram('message_latency_seconds', ...)

# Middleware coleta automaticamente:
# labels(...): Adiciona dimensões à métrica (ex: endpoint acessado).
# observe(duration): Registra o tempo que a requisição levou.
MESSAGE_LATENCY_SECONDS.labels(operation=scope['path']).observe(duration)
```

### 3.9 Extensibilidade/Manutenibilidade

**Requisito:** Clean interface, Swagger.

**Implementação:**

- **OpenAPI:** O FastAPI gera automaticamente a documentação em `/docs`.
- **Arquitetura Hexagonal (Adapters):** O código é organizado em `domain`, `services` e `adapters`, facilitando a manutenção.

*Trecho de Código (`src/main.py`):*

```python
# FastAPI(...): Inicializa a aplicação.
# Os parâmetros title e description são usados para gerar a página HTML do Swagger UI.
app = FastAPI(
    title="Chat4all - Universal Message Router",
    description="Documentação automática gerada pelo FastAPI (Swagger UI)",
    # ...
)
```
