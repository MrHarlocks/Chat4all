# Chat4all - Universal Message Router

Trabalho de Sistemas Distribuídos. Uma API robusta para roteamento de mensagens entre diferentes plataformas, suporte a arquivos grandes e gerenciamento de conversas.

## 🚀 Funcionalidades

- **Roteamento Universal**: Envio e recebimento de mensagens entre plataformas (Interno, WhatsApp, Telegram, etc.).
- **Arquivos Grandes**: Suporte para upload e download de arquivos de até 2GB via MinIO (S3).
- **Conversas em Grupo**: Criação e gerenciamento de grupos.
- **Status de Mensagem**: Rastreamento de entrega (Enviado, Entregue, Lido).
- **Escalável**: Arquitetura baseada em eventos com Apache Kafka e MongoDB.

## 📋 Pré-requisitos

- **Docker & Docker Compose** (para rodar a infraestrutura)
- **Python 3.11+**

## 🛠️ Instalação e Execução

1. **Clone o repositório e entre na pasta:**

   ```bash
   git clone https://github.com/MrHarlocks/Chat4all.git
   cd Chat4all
   ```

2. **Crie um ambiente virtual e instale as dependências:**

   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\Activate.ps1
   # Linux/Mac
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Inicie a Infraestrutura (MongoDB, Kafka, MinIO):**

   ```bash
   docker-compose up -d
   ```

   *Aguarde cerca de 30 segundos para que todos os serviços iniciem.*

4. **Inicie a API:**

   ```bash
   uvicorn src.main:app --reload
   ```

   A API estará rodando em: `http://localhost:8000`

## 📖 Documentação Interativa (Swagger UI)

Acesse `http://localhost:8000/docs` para ver a documentação completa e testar os endpoints diretamente pelo navegador.

## ⚡ Exemplos de Uso

### 1. Criar uma Conversa

```bash
curl -X POST http://localhost:8000/api/v1/conversations/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "PRIVATE",
    "participants": ["user-uuid-1", "user-uuid-2"],
    "metadata": {"title": "Chat Teste"}
  }'
```

*Copie o `id` retornado para usar nos próximos passos.*

### 2. Enviar uma Mensagem

```bash
curl -X POST http://localhost:8000/api/v1/messages/ \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "SEU_ID_DA_CONVERSA",
    "content": "Olá, mundo distribuído!",
    "attachments": []
  }'
```

### 3. Ver Histórico da Conversa

```bash
curl http://localhost:8000/api/v1/conversations/SEU_ID_DA_CONVERSA/messages
```

## 🧪 Testes

Para rodar os testes de integração (requer Docker rodando):

```bash
pytest tests/integration
```

## 🧪 Testes Avançados e Escalabilidade

### 1. Testes de Carga (Locust)

Simula múltiplos usuários enviando mensagens simultaneamente.

**Opção A: Interface Web (Interativo)**
```bash
./scripts/start_locust_ui.ps1
```
Acesse: `http://localhost:8089`

**Opção B: Linha de Comando (Automático)**
```bash
./scripts/run_load_test.ps1
```
Gera um relatório HTML na pasta `tests/load/`.

### 2. Teste de Escalabilidade Horizontal

Verifica o processamento com múltiplos workers consumidores.

```bash
# 1. Preparar o Kafka (aumentar partições)
python scripts/setup_kafka.py

# 2. Rodar o teste
python scripts/scalability_test.py
```

### 3. Teste de Tolerância a Falhas

Simula a queda de workers durante o processamento.

```bash
python scripts/fault_tolerance_test.py
```

## 📊 Monitoramento

- **Prometheus**: `http://localhost:9090` (Métricas)
- **Grafana**: `http://localhost:3000` (Dashboards)
  - Login: `admin` / `admin`
