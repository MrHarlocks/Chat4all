# Arquitetura do Sistema - Chat4all (Universal Message Router)

Este documento descreve a arquitetura técnica da API **Chat4all**, um roteador universal de mensagens projetado para alta escalabilidade, suporte a múltiplas plataformas e transferência de grandes arquivos.

## 1. Visão Geral

O **Chat4all** atua como um hub centralizado de comunicação, permitindo a troca de mensagens e arquivos entre clientes internos (Web, Mobile, CLI) e plataformas externas (WhatsApp, Telegram, Instagram, etc.). O sistema foi projetado para suportar milhões de usuários e tráfego intenso, utilizando uma arquitetura assíncrona e orientada a eventos.

## 2. Estilo Arquitetural

O projeto segue os princípios da **Arquitetura Hexagonal (Ports and Adapters)** e **Clean Architecture**. Isso garante que a lógica de negócios (Core) permaneça isolada de detalhes de infraestrutura e implementações externas.

### Camadas do Sistema

1. **API (Interface de Entrada)**:
    * Responsável por receber requisições HTTP (REST) ou gRPC.
    * Valida dados de entrada e autentica usuários (JWT).
    * Encaminha comandos para a camada de Serviços.
    * *Tecnologia*: FastAPI.

2. **Services (Lógica de Aplicação)**:
    * Orquestra os fluxos de negócio (ex: enviar mensagem, criar grupo).
    * Não conhece detalhes de banco de dados ou APIs externas.
    * Interage com o Domínio e as Portas (Interfaces).

3. **Domain (Núcleo do Negócio)**:
    * Contém as entidades fundamentais: `User`, `Conversation`, `Message`.
    * Define as regras de negócio puras e interfaces (Ports) que os adaptadores devem implementar.

4. **Adapters (Infraestrutura)**:
    * Implementam as interfaces definidas pelo Domínio.
    * **Database Adapter**: Repositórios para MongoDB.
    * **Messaging Adapter**: Produtores e Consumidores Kafka.
    * **Storage Adapter**: Cliente S3/MinIO para arquivos.
    * **Platform Adapters**: Integrações específicas com WhatsApp, Telegram, etc.

## 3. Componentes de Infraestrutura

A arquitetura é composta pelos seguintes serviços containerizados:

* **API Service (Python/FastAPI)**: O servidor de aplicação principal. É stateless (sem estado), permitindo escalabilidade horizontal (adicionar mais réplicas conforme a carga aumenta).
* **MongoDB**: Banco de dados NoSQL orientado a documentos. Escolhido pela alta performance de escrita e flexibilidade de schema para armazenar históricos de chat e metadados.
* **Apache Kafka**: Message Broker distribuído. Atua como a espinha dorsal do sistema, desacoplando o recebimento da mensagem do seu processamento e envio. Garante que picos de tráfego não derrubem o sistema e permite retentativas em caso de falha.
* **MinIO (S3 Compatible)**: Object Storage para arquivos. Permite o armazenamento e streaming de arquivos grandes (até 2GB) sem sobrecarregar a memória da API ou o banco de dados.
* **Zookeeper**: Gerenciador de coordenação para o cluster Kafka.

## 4. Fluxo de Dados (Pipeline de Mensagem)

1. **Ingestão**: O cliente (interno ou webhook externo) envia uma mensagem para a API.
2. **Validação e Persistência**: A API valida a requisição e o `MessageService` persiste a mensagem no MongoDB com status `PENDING`.
3. **Enfileiramento**: A mensagem é publicada em um tópico do Kafka (`message.events`).
4. **Roteamento**: O `RouterService` (consumidor Kafka) lê a mensagem.
5. **Despacho**: Com base no destinatário, o roteador seleciona o `PlatformAdapter` correto (ex: TelegramAdapter).
6. **Entrega**: O adaptador envia a mensagem para a API externa.
7. **Confirmação**: Após o sucesso, o status da mensagem no MongoDB é atualizado para `SENT` ou `DELIVERED`.

### 4.1 Fluxo de Status (Feedback Loop)

1. **Evento Externo**: A plataforma externa (ex: WhatsApp) envia um webhook informando mudança de status (ex: `READ`).
2. **Ingestão de Webhook**: O endpoint `/webhooks/{provider}` recebe o evento.
3. **Processamento**: O sistema identifica a mensagem original pelo ID.
4. **Atualização**: O status da mensagem é atualizado no banco de dados (ex: de `DELIVERED` para `READ`).
5. **Notificação (Futuro)**: O novo status pode ser enviado via WebSocket para o cliente remetente.

## 5. Escalabilidade e Desempenho

* **Assincronismo**: O uso de `asyncio` no Python e do Kafka permite que a API processe milhares de conexões simultâneas sem bloquear threads.
* **Streaming de Arquivos**: Uploads e downloads são feitos via streaming, transmitindo dados em pedaços (chunks), mantendo o uso de memória baixo mesmo para arquivos de 2GB.
* **Escala Horizontal**: Tanto a API quanto os consumidores Kafka podem ser escalados horizontalmente para processar mais mensagens em paralelo.

## 6. Modelo de Dados Simplificado

* **User**: Identidade única no sistema.
* **Conversation**: Agrupador de mensagens. Pode ser `PRIVATE` (1-1) ou `GROUP` (1-N).
* **Message**: Unidade atômica de comunicação. Possui remetente, conteúdo, timestamp e status.
* **Attachment**: Metadados de arquivos anexados (URL, tamanho, tipo MIME).

---
*Documento gerado automaticamente com base na implementação atual da branch `001-universal-message-router`.*
