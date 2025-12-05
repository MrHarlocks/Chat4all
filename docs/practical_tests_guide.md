# Guia de Testes Práticos - Validação de Requisitos

Este guia fornece instruções passo a passo para validar cada requisito funcional e não-funcional do sistema **Chat4all** utilizando os scripts de teste e ferramentas disponíveis no projeto.

---

## 1. Requisitos Funcionais

### 2.1 Mensageria Básica & 2.4 Persistência
**Objetivo:** Verificar o envio de mensagens e sua gravação no banco de dados.

*   **Teste Automatizado:**
    Execute o teste de integração que simula o ciclo completo de envio.
    ```powershell
    python -m pytest tests/integration/test_send_message.py -v
    ```

*   **Teste Manual (Swagger UI):**
    1.  Acesse `http://localhost:8000/docs`.
    2.  Use o endpoint `POST /api/v1/conversations` para criar uma conversa.
    3.  Copie o `id` da conversa.
    4.  Use o endpoint `POST /api/v1/messages` com o `conversation_id`.
    5.  **Validação:** Verifique se a resposta é `200 OK` e se o status inicial é `PENDING`.

### 2.2 Controle de Envio / Entrega / Leitura
**Objetivo:** Validar a atualização de status da mensagem (Idempotência e Ciclo de Vida).

*   **Teste Automatizado:**
    Execute o teste de ciclo de vida completo.
    ```powershell
    python -m pytest tests/integration/test_full_lifecycle.py -v
    ```
    *Este teste envia uma mensagem e aguarda (polling) até que o status mude para SENT/DELIVERED.*

### 2.3 Multiplataforma e Roteamento
**Objetivo:** Garantir que o sistema aceita diferentes plataformas (WhatsApp, Instagram, Mock).

*   **Teste Manual:**
    1.  No Swagger (`/docs`), envie uma mensagem com `"platform": "WHATSAPP"`.
    2.  Envie outra com `"platform": "INTERNAL"`.
    3.  **Validação:** Observe nos logs do container `api` ou `worker` (via Docker Desktop ou `docker logs`) que o `WhatsAppProvider` e `MockProvider` foram instanciados respectivamente.

### 2.5 API Pública
**Objetivo:** Verificar a exposição e documentação da API.

*   **Teste Prático:**
    1.  Abra o navegador em `http://localhost:8000/docs`.
    2.  **Validação:** A interface Swagger UI deve carregar, listando todos os endpoints (`/conversations`, `/messages`, `/files`).
    3.  Baixe o arquivo OpenAPI em `http://localhost:8000/openapi.json`.

### 3.6 Armazenamento de Arquivos
**Objetivo:** Testar o fluxo de upload via Presigned URL (MinIO/S3).

*   **Teste Automatizado:**
    ```powershell
    python -m pytest tests/integration/test_files.py -v
    ```
    *Este teste solicita uma URL de upload, faz o upload do arquivo binário e confirma a persistência.*

---

## 2. Requisitos Não-Funcionais (NFR)

### 3.1 Escalabilidade
**Objetivo:** Demonstrar que o sistema suporta aumento de carga adicionando consumidores.

*   **Teste Prático (Script Dedicado):**
    Este script inicia múltiplos workers e mede o tempo de processamento de um lote de mensagens.
    ```powershell
    python scripts/scalability_test.py
    ```
    **Resultado Esperado:** O script exibirá um gráfico ou log mostrando que o throughput aumenta (ou a latência diminui) conforme mais workers são adicionados.

### 3.2 Alta Disponibilidade / Tolerância a Falhas
**Objetivo:** Verificar se o sistema continua funcionando mesmo se um componente falhar.

*   **Teste Prático (Chaos Engineering):**
    Este script inicia o sistema, começa a enviar mensagens e "mata" um processo worker aleatoriamente durante a execução.
    ```powershell
    python scripts/fault_tolerance_test.py
    ```
    **Resultado Esperado:** O script deve reportar que todas as mensagens foram processadas eventualmente, mesmo com a queda de um worker (recuperação via rebalanceamento do Kafka).

### 3.4 Latência & 3.5 Throughput
**Objetivo:** Medir a performance sob carga pesada.

*   **Teste de Carga (Locust):**
    1.  Inicie o teste de carga:
        ```powershell
        ./scripts/run_load_test.ps1
        ```
    2.  Isso executará o Locust em modo headless por um tempo determinado.
    3.  **Validação:** Ao final, um relatório HTML será gerado em `tests/load/`, mostrando RPS (Requests per Second) e latência média/p99.

### 3.7 Operacional / Observabilidade
**Objetivo:** Visualizar métricas em tempo real.

*   **Teste Prático:**
    1.  Certifique-se de que os containers estão rodando (`docker-compose up -d`).
    2.  Gere tráfego (pode usar o `./scripts/run_load_test.ps1` ou enviar mensagens manualmente).
    3.  Acesse o Grafana: `http://localhost:3000` (admin/admin).
    4.  Vá para o Dashboard **Chat4all Metrics**.
    5.  **Validação:** Os gráficos de "Messages Processed per Second" e "API Latency" devem mostrar dados.

---

## Resumo de Comandos

| Requisito | Comando / Ação |
| :--- | :--- |
| **Funcional (Geral)** | `pytest tests/integration/` |
| **Escalabilidade** | `python scripts/scalability_test.py` |
| **Tolerância a Falhas** | `python scripts/fault_tolerance_test.py` |
| **Carga (Latência/Throughput)** | `./scripts/run_load_test.ps1` |
| **Observabilidade** | Acessar `http://localhost:3000` |
