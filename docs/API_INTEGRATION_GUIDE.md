# API Integration Guide

Guia completo para integração com as APIs do sistema LiteLMM.

## Índice

- [Visão Geral](#visão-geral)
- [Autenticação](#autenticação)
- [Endpoints Disponíveis](#endpoints-disponíveis)
  - [1. Listar Modelos](#1-listar-modelos)
  - [2. Chat Completion com Modelo](#2-chat-completion-com-modelo)
  - [3. Listar Agents Disponíveis](#3-listar-agents-disponíveis)
  - [4. Consultar Detalhes de um Agent](#4-consultar-detalhes-de-um-agent)
  - [5. Chat Completion com Agent](#5-chat-completion-com-agent)
- [Exemplos de Integração](#exemplos-de-integração)
- [Tratamento de Erros](#tratamento-de-erros)

## Visão Geral

O sistema LiteLMM oferece duas formas principais de interação:

1. **Modelos Diretos**: Chat com modelos LLM (Claude, GPT) diretamente
2. **Agents**: Chat com agents especializados que podem usar MCPs e contexto adicional

**Base URL**: `http://localhost:8000`

### ⚠️ Header Obrigatório em Todas as Requisições

Para garantir a auditoria, controle de cotas e orquestração de dados, **todas as requisições** devem incluir o seguinte header:

```http
X-OpenWebUI-User-Email: usuario@example.com
```

```http
X-OpenWebUI-User-Email: usuario@example.com
```

## Endpoints Disponíveis

### 1. Listar Modelos

Retorna a lista de modelos LLM disponíveis para uso.

#### Request

```http
GET /v1/models
```

#### Response

```json
{
  "data": [
    {
      "id": "claude-3-haiku",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    },
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    }
  ],
  "object": "list"
}
```

#### Exemplo (curl)

```bash
curl http://localhost:8000/v1/models
```

#### Exemplo (Python)

```python
import requests

response = requests.get("http://localhost:8000/v1/models")
models = response.json()

for model in models['data']:
    print(f"Model: {model['id']}")
```

#### Exemplo (JavaScript)

```javascript
fetch('http://localhost:8000/v1/models')
  .then(response => response.json())
  .then(data => {
    data.data.forEach(model => {
      console.log(`Model: ${model.id}`);
    });
  });
```

---

### 2. Chat Completion com Modelo

Envia uma mensagem para um modelo LLM e recebe a resposta.

#### Request

```http
POST /v1/chat/completions
Content-Type: application/json
```

```json
{
  "model": "claude-3-haiku",
  "messages": [
    {
      "role": "user",
      "content": "Sua pergunta aqui"
    }
  ],
  "stream": false
}
```

#### Parâmetros

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `model` | string | Sim | ID do modelo (obtido via `/v1/models`) |
| `messages` | array | Sim | Array de mensagens (histórico da conversa) |
| `messages[].role` | string | Sim | Papel: "user", "assistant" ou "system" |
| `messages[].content` | string | Sim | Conteúdo da mensagem |
| `stream` | boolean | Não | Se `true`, retorna resposta em streaming (default: false) |

#### Response (stream: false)

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "claude-3-haiku",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Resposta do modelo aqui"
      },
      "finish_reason": "stop"
    }
  ]
}
```

#### Response (stream: true)

Formato Server-Sent Events (SSE):

```
data: {"id":"chatcmpl-123","created":1677652288,"model":"claude-3-haiku","choices":[{"index":0,"delta":{"content":"Olá"}}]}

data: {"id":"chatcmpl-123","created":1677652288,"model":"claude-3-haiku","choices":[{"index":0,"delta":{"content":"!"}}]}

data: [DONE]
```

#### Exemplo (curl)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-haiku",
    "messages": [
      {"role": "user", "content": "Olá, como você está?"}
    ],
    "stream": false
  }'
```

#### Exemplo (Python)

```python
import requests

payload = {
    "model": "claude-3-haiku",
    "messages": [
        {"role": "user", "content": "Explique o que é machine learning"}
    ],
    "stream": False
}

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json=payload
)

result = response.json()
answer = result['choices'][0]['message']['content']
print(answer)
```

#### Exemplo (Python - Streaming)

```python
import requests
import json

payload = {
    "model": "claude-3-haiku",
    "messages": [
        {"role": "user", "content": "Conte uma história curta"}
    ],
    "stream": True
}

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json=payload,
    stream=True
)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]

            if data_str == '[DONE]':
                break

            try:
                data = json.loads(data_str)
                content = data['choices'][0]['delta'].get('content', '')
                if content:
                    print(content, end='', flush=True)
            except json.JSONDecodeError:
                pass
```

#### Exemplo (JavaScript)

```javascript
// Non-streaming
fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'claude-3-haiku',
    messages: [
      { role: 'user', content: 'O que é inteligência artificial?' }
    ],
    stream: false
  })
})
.then(response => response.json())
.then(data => {
  console.log(data.choices[0].message.content);
});

// Streaming
fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'claude-3-haiku',
    messages: [
      { role: 'user', content: 'Conte uma história' }
    ],
    stream: true
  })
})
.then(response => {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  return reader.read().then(function processText({ done, value }) {
    if (done) return;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    lines.forEach(line => {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices[0].delta?.content || '';
          if (content) console.log(content);
        } catch (e) {}
      }
    });

    return reader.read().then(processText);
  });
});
```

---

### 3. Listar Agents Disponíveis

Retorna a lista de agents que o usuário tem permissão para acessar.

#### Request

```http
GET /api/agents
X-OpenWebUI-User-Email: usuario@example.com
```

#### Response

```json
{
  "success": true,
  "agents": [
    {
      "id": "diagnostico-vendas",
      "name": "Diagnóstico de Vendas",
      "description": "Agent especializado em análise de vendas e métricas de performance",
      "llm_model": "claude-3-haiku",
      "llm_provider": "anthropic",
      "prompt_count": 3
    }
  ]
}
```

#### Exemplo (curl)

```bash
curl http://localhost:8000/api/agents \
  -H "X-OpenWebUI-User-Email: emingues@gmail.com"
```

#### Exemplo (Python)

```python
import requests

headers = {
    "X-OpenWebUI-User-Email": "emingues@gmail.com"
}

response = requests.get(
    "http://localhost:8000/api/agents",
    headers=headers
)

data = response.json()
agents = data['agents']

for agent in agents:
    print(f"Agent: {agent['name']}")
    print(f"  ID: {agent['id']}")
    print(f"  Model: {agent['llm_provider']}/{agent['llm_model']}")
    print(f"  Prompts: {agent['prompt_count']}")
```

#### Exemplo (JavaScript)

```javascript
fetch('http://localhost:8000/api/agents', {
  headers: {
    'X-OpenWebUI-User-Email': 'emingues@gmail.com'
  }
})
.then(response => response.json())
.then(data => {
  data.agents.forEach(agent => {
    console.log(`Agent: ${agent.name}`);
    console.log(`  ID: ${agent.id}`);
    console.log(`  Model: ${agent.llm_provider}/${agent.llm_model}`);
  });
});
```

---

### 4. Consultar Detalhes de um Agent

Retorna informações detalhadas sobre um agent específico, incluindo seus prompts sugeridos.

#### Request

```http
GET /api/agents/{agent_id}
X-OpenWebUI-User-Email: usuario@example.com
```

#### Response

```json
{
  "success": true,
  "agent": {
    "id": "diagnostico-vendas",
    "name": "Diagnóstico de Vendas",
    "description": "Agent especializado em análise de vendas e métricas de performance",
    "llm_model": "claude-3-haiku",
    "llm_provider": "anthropic",
    "prompts": [
      {
        "title": "Top Produtos",
        "content": "Quais são os produtos mais vendidos nos últimos 30 dias?"
      },
      {
        "title": "Faturamento Mensal",
        "content": "Qual foi o faturamento total do último mês?"
      },
      {
        "title": "Performance por Categoria",
        "content": "Quais categorias tiveram melhor performance?"
      }
    ]
  }
}
```

#### Exemplo (curl)

```bash
curl http://localhost:8000/api/agents/diagnostico-vendas \
  -H "X-OpenWebUI-User-Email: emingues@gmail.com"
```

#### Exemplo (Python)

```python
import requests

headers = {
    "X-OpenWebUI-User-Email": "emingues@gmail.com"
}

response = requests.get(
    "http://localhost:8000/api/agents/diagnostico-vendas",
    headers=headers
)

data = response.json()
agent = data['agent']

print(f"Agent: {agent['name']}")
print(f"Description: {agent['description']}")
print(f"\nPrompts sugeridos:")

for i, prompt in enumerate(agent['prompts'], 1):
    print(f"{i}. {prompt['title']}")
    print(f"   {prompt['content']}")
```

#### Exemplo (JavaScript)

```javascript
fetch('http://localhost:8000/api/agents/diagnostico-vendas', {
  headers: {
    'X-OpenWebUI-User-Email': 'emingues@gmail.com'
  }
})
.then(response => response.json())
.then(data => {
  const agent = data.agent;
  console.log(`Agent: ${agent.name}`);
  console.log(`Description: ${agent.description}`);

  console.log('\nPrompts sugeridos:');
  agent.prompts.forEach((prompt, index) => {
    console.log(`${index + 1}. ${prompt.title}`);
    console.log(`   ${prompt.content}`);
  });
});
```

---

### 5. Chat Completion com Agent

Envia uma mensagem para um agent especializado. Agents podem usar MCPs, contexto adicional e têm prompts system personalizados.

#### Request

```http
POST /v1/chat/completions
Content-Type: application/json
X-OpenWebUI-User-Email: usuario@example.com
```

```json
{
  "model": "diagnostico-vendas",
  "messages": [
    {
      "role": "user",
      "content": "Quais foram os produtos mais vendidos?"
    }
  ],
  "stream": true
}
```

#### Parâmetros

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `model` | string | Sim | ID do agent (obtido via `/api/agents`) |
| `messages` | array | Sim | Array de mensagens (histórico da conversa) |
| `messages[].role` | string | Sim | Papel: "user" ou "assistant" |
| `messages[].content` | string | Sim | Conteúdo da mensagem |
| `stream` | boolean | Não | Se `true`, retorna resposta em streaming |

**Nota**: Agents sempre retornam respostas em formato streaming (SSE).

#### Response

Formato Server-Sent Events (SSE):

```
data: {"id":"chatcmpl-123","created":1677652288,"model":"claude-3-haiku","choices":[{"index":0,"delta":{"content":"Análise","role":"assistant"}}]}

data: {"id":"chatcmpl-123","created":1677652288,"model":"claude-3-haiku","choices":[{"index":0,"delta":{"content":" dos"}}]}

data: {"id":"chatcmpl-123","created":1677652288,"model":"claude-3-haiku","choices":[{"index":0,"delta":{"content":" produtos..."}}]}

data: [DONE]
```

#### Exemplo (curl)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-OpenWebUI-User-Email: emingues@gmail.com" \
  -d '{
    "model": "diagnostico-vendas",
    "messages": [
      {"role": "user", "content": "Qual foi o faturamento do mês passado?"}
    ],
    "stream": true
  }'
```

#### Exemplo (Python)

```python
import requests
import json

headers = {
    "X-OpenWebUI-User-Email": "emingues@gmail.com"
}

payload = {
    "model": "diagnostico-vendas",
    "messages": [
        {"role": "user", "content": "Quais produtos tiveram melhor performance?"}
    ],
    "stream": True
}

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json=payload,
    headers=headers,
    stream=True
)

print("Agent response:")
for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            data_str = line_str[6:]

            if data_str == '[DONE]':
                break

            try:
                data = json.loads(data_str)
                content = data['choices'][0]['delta'].get('content', '')
                if content:
                    print(content, end='', flush=True)
            except json.JSONDecodeError:
                pass

print()  # Nova linha no final
```

#### Exemplo (JavaScript)

```javascript
fetch('http://localhost:8000/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-OpenWebUI-User-Email': 'emingues@gmail.com'
  },
  body: JSON.stringify({
    model: 'diagnostico-vendas',
    messages: [
      { role: 'user', content: 'Analise as vendas do último trimestre' }
    ],
    stream: true
  })
})
.then(response => {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  return reader.read().then(function processText({ done, value }) {
    if (done) {
      console.log('\nStream completo');
      return;
    }

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    lines.forEach(line => {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;

        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices[0].delta?.content || '';
          if (content) process.stdout.write(content);
        } catch (e) {}
      }
    });

    return reader.read().then(processText);
  });
});
```

---

## Exemplos de Integração

### Exemplo Completo: Chatbot com Agent

```python
import requests
import json

class AgentClient:
    def __init__(self, base_url, user_email):
        self.base_url = base_url
        self.user_email = user_email
        self.headers = {
            "X-OpenWebUI-User-Email": user_email
        }

    def list_agents(self):
        """Lista agents disponíveis"""
        response = requests.get(
            f"{self.base_url}/api/agents",
            headers=self.headers
        )
        return response.json()['agents']

    def get_agent_details(self, agent_id):
        """Obtém detalhes de um agent"""
        response = requests.get(
            f"{self.base_url}/api/agents/{agent_id}",
            headers=self.headers
        )
        return response.json()['agent']

    def chat(self, agent_id, message, history=None):
        """Envia mensagem para agent"""
        if history is None:
            history = []

        messages = history + [
            {"role": "user", "content": message}
        ]

        payload = {
            "model": agent_id,
            "messages": messages,
            "stream": True
        }

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers=self.headers,
            stream=True
        )

        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]

                    if data_str == '[DONE]':
                        break

                    try:
                        data = json.loads(data_str)
                        content = data['choices'][0]['delta'].get('content', '')
                        if content:
                            print(content, end='', flush=True)
                            full_response += content
                    except json.JSONDecodeError:
                        pass

        print()  # Nova linha
        return full_response


# Uso
client = AgentClient(
    base_url="http://localhost:8000",
    user_email="emingues@gmail.com"
)

# Lista agents
agents = client.list_agents()
print("Agents disponíveis:")
for agent in agents:
    print(f"  - {agent['name']} ({agent['id']})")

# Conversa com agent
print("\nIniciando conversa com diagnostico-vendas...")
print("User: Quais foram os produtos mais vendidos?")
print("Agent: ", end="")

response = client.chat(
    agent_id="diagnostico-vendas",
    message="Quais foram os produtos mais vendidos?"
)
```

### Exemplo Completo: React Hook

```javascript
// useAgent.js
import { useState, useCallback } from 'react';

export function useAgent(baseUrl, userEmail) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const listAgents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${baseUrl}/api/agents`, {
        headers: {
          'X-OpenWebUI-User-Email': userEmail
        }
      });

      const data = await response.json();
      return data.agents;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [baseUrl, userEmail]);

  const chat = useCallback(async (agentId, message, onChunk) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${baseUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-OpenWebUI-User-Email': userEmail
        },
        body: JSON.stringify({
          model: agentId,
          messages: [{ role: 'user', content: message }],
          stream: true
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;

            try {
              const parsed = JSON.parse(data);
              const content = parsed.choices[0].delta?.content || '';

              if (content) {
                fullResponse += content;
                if (onChunk) onChunk(content, fullResponse);
              }
            } catch (e) {}
          }
        }
      }

      return fullResponse;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [baseUrl, userEmail]);

  return { listAgents, chat, loading, error };
}

// Uso do hook
function ChatComponent() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const { chat, loading } = useAgent(
    'http://localhost:8000',
    'emingues@gmail.com'
  );

  const handleSend = async () => {
    setResponse('');

    await chat(
      'diagnostico-vendas',
      message,
      (chunk, fullResponse) => {
        setResponse(fullResponse);
      }
    );
  };

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Digite sua mensagem..."
      />
      <button onClick={handleSend} disabled={loading}>
        Enviar
      </button>
      <div>{response}</div>
    </div>
  );
}
```

---

## Tratamento de Erros

### Códigos de Status HTTP

| Código | Descrição | Ação Recomendada |
|--------|-----------|------------------|
| 200 | Sucesso | Continue normalmente |
| 400 | Requisição inválida | Verifique os parâmetros enviados |
| 401 | Não autorizado | Verifique o header `X-OpenWebUI-User-Email` |
| 403 | Acesso negado | Usuário não tem permissão para acessar o recurso |
| 404 | Não encontrado | Agent ou modelo não existe |
| 429 | Quota excedida | Aguarde antes de fazer nova requisição |
| 500 | Erro interno | Tente novamente mais tarde |

### Formato de Erro

```json
{
  "error": {
    "message": "Descrição do erro",
    "type": "tipo_do_erro",
    "param": "parametro_com_problema",
    "code": "400"
  }
}
```

### Exemplo de Tratamento de Erros (Python)

```python
import requests

def safe_chat(agent_id, message, user_email):
    try:
        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            json={
                "model": agent_id,
                "messages": [{"role": "user", "content": message}],
                "stream": True
            },
            headers={"X-OpenWebUI-User-Email": user_email},
            stream=True,
            timeout=30
        )

        response.raise_for_status()

        # Processar resposta...

    except requests.exceptions.Timeout:
        print("Erro: Tempo limite excedido")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Erro: Autenticação necessária")
        elif e.response.status_code == 403:
            print("Erro: Acesso negado")
        elif e.response.status_code == 404:
            print("Erro: Agent não encontrado")
        else:
            print(f"Erro HTTP {e.response.status_code}: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")
```

### Exemplo de Tratamento de Erros (JavaScript)

```javascript
async function safeChat(agentId, message, userEmail) {
  try {
    const response = await fetch('http://localhost:8000/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-OpenWebUI-User-Email': userEmail
      },
      body: JSON.stringify({
        model: agentId,
        messages: [{ role: 'user', content: message }],
        stream: true
      })
    });

    if (!response.ok) {
      const error = await response.json();

      switch (response.status) {
        case 401:
          throw new Error('Autenticação necessária');
        case 403:
          throw new Error('Acesso negado');
        case 404:
          throw new Error('Agent não encontrado');
        case 429:
          throw new Error('Quota excedida, tente novamente mais tarde');
        default:
          throw new Error(error.error?.message || 'Erro desconhecido');
      }
    }

    // Processar resposta...

  } catch (error) {
    if (error.name === 'TypeError') {
      console.error('Erro de conexão:', error.message);
    } else {
      console.error('Erro:', error.message);
    }
  }
}
```

---

## Notas Importantes

1. **Streaming**: Agents sempre retornam respostas em streaming. Modelos diretos podem usar streaming opcional.

2. **Histórico de Conversa**: O sistema não mantém histórico automaticamente. Você deve enviar todo o histórico relevante em cada requisição.

3. **Rate Limiting**: O sistema pode ter limites de taxa. Implemente retry com backoff exponencial.

4. **Timeouts**: Configure timeouts adequados (30-60 segundos) para chamadas de chat.

5. **Permissões**: Agents são filtrados por grupo. Apenas agents que o usuário tem permissão serão retornados.

6. **Modelos vs Agents**:
   - Use **modelos** para chat genérico
   - Use **agents** para tarefas especializadas que podem precisar de contexto adicional (MCPs, dados, etc)

---

## Suporte

Para dúvidas ou problemas:
- Verifique os logs do sistema: `docker-compose logs -f`
- Consulte a documentação adicional em `/docs`
- Abra um issue no repositório do projeto
