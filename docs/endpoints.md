# Documentação dos Endpoints - Chat4all

Este documento detalha os endpoints disponíveis na API do **Chat4all**. A API segue os princípios REST e utiliza JSON para troca de dados.

## Base URL
`http://localhost:8000/api/v1`

---

## 1. Conversas (Conversations)

Gerenciamento de conversas privadas e grupos.

### Criar Conversa
Cria uma nova conversa entre usuários.

*   **URL**: `/conversations/`
*   **Método**: `POST`
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "type": "PRIVATE", // ou "GROUP"
      "participants": ["uuid-user-1", "uuid-user-2"],
      "metadata": {
        "title": "Nome do Grupo (opcional)"
      }
    }
    ```
*   **Resposta (201 Created)**: Objeto `Conversation` criado.

### Listar Mensagens da Conversa
Recupera o histórico de mensagens de uma conversa específica.

*   **URL**: `/conversations/{conversation_id}/messages`
*   **Método**: `GET`
*   **Parâmetros de Query**:
    *   `limit`: Número máximo de mensagens (padrão: 50, máx: 100).
    *   `skip`: Número de mensagens para pular (paginação).
*   **Resposta (200 OK)**: Lista de objetos `Message`.

---

## 2. Mensagens (Messages)

Envio e recuperação de mensagens individuais.

### Enviar Mensagem
Envia uma nova mensagem para uma conversa existente.

*   **URL**: `/messages/`
*   **Método**: `POST`
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "conversation_id": "uuid-da-conversa",
      "content": "Olá, mundo!",
      "attachments": [] // Lista de anexos (opcional)
    }
    ```
*   **Resposta (201 Created)**: Objeto `Message` com status `PENDING`.

### Buscar Mensagem por ID
Recupera os detalhes de uma mensagem específica.

*   **URL**: `/messages/{message_id}`
*   **Método**: `GET`
*   **Resposta (200 OK)**: Objeto `Message`.

---

## 3. Arquivos (Files)

Gerenciamento de upload de arquivos grandes.

### Gerar URL de Upload
Gera uma URL pré-assinada (Presigned URL) para fazer upload direto para o Storage (MinIO/S3).

*   **URL**: `/files/upload-url`
*   **Método**: `POST`
*   **Corpo da Requisição (JSON)**:
    ```json
    {
      "filename": "video.mp4",
      "mime_type": "video/mp4",
      "size": 10485760 // Tamanho em bytes
    }
    ```
*   **Resposta (200 OK)**:
    ```json
    {
      "upload_url": "http://minio:9000/...",
      "file_id": "uuid-do-arquivo",
      "public_url": "http://localhost:9000/...",
      "object_name": "caminho/no/bucket/video.mp4"
    }
    ```

---

## 4. Webhooks

Integração com plataformas externas.

### Receber Webhook
Endpoint genérico para receber eventos de plataformas externas (WhatsApp, Telegram, etc.).

*   **URL**: `/webhooks/{provider}`
*   **Método**: `POST`
*   **Parâmetros de Rota**:
    *   `provider`: Nome do provedor (ex: `whatsapp`, `telegram`).
*   **Corpo da Requisição**: Payload JSON enviado pelo provedor.
*   **Resposta (200 OK)**: Confirmação de recebimento.

---

## Modelos de Dados Principais

### Conversation
```json
{
  "id": "uuid",
  "type": "PRIVATE",
  "participants": ["uuid-1", "uuid-2"],
  "created_at": "2023-10-27T10:00:00Z",
  "metadata": {}
}
```

### Message
```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "sender_id": "uuid",
  "content": "Texto da mensagem",
  "timestamp": "2023-10-27T10:05:00Z",
  "status": "SENT",
  "attachments": []
}
```
