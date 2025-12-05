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
success = await provider.send_message(message)

# Define o novo status com base no sucesso do envio
new_status = MessageStatus.SENT if success else MessageStatus.FAILED

# repository.update_status(...): Atualiza atomicamente o campo 'status' no documento do MongoDB
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
    Platform.INTERNAL.value: MockProvider(),       # Simula envio interno
    Platform.WHATSAPP.value: WhatsAppProvider(),   # Adaptador Meta API
    Platform.INSTAGRAM.value: InstagramProvider(), # Adaptador Instagram Graph API
}

# Lógica de Roteamento:
    # Chama o método padronizado da interface, independente da plataforma subjacente.
    await provider.send_message(message)
```

**Alternativas e Justificativa:**
- **Alternativa:** *Blocos If/Else gigantes* ou *Microserviços separados por canal*.
- **Por que escolhemos Strategy Pattern:** *If/Else* torna o código inmanutenível rapidamente. *Microserviços* adicionariam latência de rede e complexidade operacional desnecessária neste estágio. O **Strategy Pattern** permite adicionar novos canais (ex: Telegram) apenas criando uma nova classe, sem tocar no código de roteamento existente (Open/Closed Principle).

### 2.4 Persistência padronizado da interface, independente da plataforma subjacente.
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
    # Insere o documento de forma assíncrona, liberando o Event Loop durante a I/O.
    await self.collection.insert_one(message_dict)
    return message
```

**Alternativas e Justificativa:**
- **Alternativa:** *Armazenar arquivos como BLOBs no Banco* ou *Filesystem local*.
- **Por que escolhemos S3/MinIO:** BLOBs incham o banco de dados, tornando backups lentos e caros. Filesystem local não escala horizontalmente (se a API escalar para 2 máquinas, uma não vê o arquivo da outra). **Object Storage (S3)** é o padrão da indústria para escalabilidade infinita e baixo custo de armazenamento.

### 2.5 API Pública

**Requisito:** API REST para operações.

**Implementação:**

- **FastAPI:** Framework utilizado para expor endpoints RESTful.
- **Endpoints:** `/conversations`, `/messages`, `/files`.

*Trecho de Código (`src/api/v1/router.py`):*

api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
```

**Alternativas e Justificativa:**
- **Alternativa:** *Flask* ou *Django*.
- **Por que escolhemos FastAPI:** Flask é síncrono por padrão (bloqueante). Django é robusto mas pesado ("baterias inclusas"). **FastAPI** é nativamente assíncrono (performance próxima a NodeJS/Go), usa **Pydantic** para validação automática (menos código de boilerplate) e gera Swagger automaticamente, acelerando a integração com o Frontend.

### 2.6 Extensibilidade de Canais

**Requisito:** Arquitetura de plugins/adapters.

**Implementação:**

- **Interface:** A classe abstrata `MessageProvider` define o contrato que qualquer novo canal deve seguir.

*Trecho de Código (`src/domain/interfaces/provider.py`):*

```python
    @abstractmethod
    async def send_file(self, message: Message, file_url: str) -> bool:
        pass
```

**Alternativas e Justificativa:**
- **Alternativa:** *Duck Typing* (Python padrão) ou *Herança Concreta*.
- **Por que escolhemos Classes Abstratas (ABC):** Duck typing pode causar erros em tempo de execução se um método faltar. **ABCs** garantem que o contrato seja validado em tempo de inicialização/importação, impedindo que a aplicação suba se um novo adaptador estiver incompleto.

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
MESSAGES_PROCESSED_TOTAL = Counter('messages_processed_total', ...)

# Histogram: Agrupa observações (como latência) em buckets para calcular percentis (P95, P99).
MESSAGE_LATENCY_SECONDS = Histogram('message_latency_seconds', ...)

# Middleware coleta automaticamente:
# labels(...): Adiciona dimensões à métrica (ex: endpoint acessado).
# observe(duration): Registra o tempo que a requisição levou.
MESSAGE_LATENCY_SECONDS.labels(operation=scope['path']).observe(duration)
```

**Alternativas e Justificativa:**
- **Alternativa:** *ELK Stack (Elasticsearch)* ou *SaaS (Datadog, New Relic)*.
- **Por que escolhemos Prometheus/Grafana:** ELK é focado em logs e muito pesado. SaaS é caro. **Prometheus** é o padrão cloud-native para métricas (time-series), leve e open-source, integrando perfeitamente com Kubernetes no futuro.

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

**Alternativas e Justificativa:**
- **Alternativa:** *MVC (Model-View-Controller)* ou *Monólito em Camadas*.
- **Por que escolhemos Arquitetura Hexagonal (Ports & Adapters):** MVC acopla a lógica de negócio ao framework web. A **Arquitetura Hexagonal** isola o `domain` (regras de negócio) de detalhes externos como Banco de Dados ou API. Isso permite testar a lógica de negócio sem subir o banco e trocar o Kafka por RabbitMQ (ou vice-versa) mexendo apenas nos adaptadores, sem risco de quebrar a regra de negócio.
