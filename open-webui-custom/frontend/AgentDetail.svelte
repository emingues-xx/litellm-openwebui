<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';

  let agent = null;
  let loading = true;
  let error = null;

  $: agentId = $page.params.agentId;

  async function fetchAgentDetails() {
    try {
      const response = await fetch(`/api/agents/${agentId}`);

      if (response.ok) {
        const data = await response.json();
        agent = data.agent;
      } else {
        error = 'Agent not found';
      }
    } catch (e) {
      console.error('Error fetching agent details:', e);
      error = 'Error loading agent';
    } finally {
      loading = false;
    }
  }

  async function startChatWithPrompt(promptContent) {
    try {
      // Create new chat with the agent and prompt
      const response = await fetch(`/api/agents/${agentId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          prompt: promptContent
        })
      });

      if (response.ok) {
        const data = await response.json();

        // Navigate to chat with pre-filled message
        // Open WebUI will handle creating the chat
        goto(`/c/new?model=${data.model}&message=${encodeURIComponent(data.message)}`);
      }
    } catch (e) {
      console.error('Error starting chat:', e);
    }
  }

  onMount(() => {
    fetchAgentDetails();
  });
</script>

<div class="agent-detail">
  {#if loading}
    <div class="loading-container">
      <div class="spinner"></div>
      <span>Loading agent...</span>
    </div>
  {:else if error}
    <div class="error-container">
      <h2>Error</h2>
      <p>{error}</p>
      <button on:click={() => goto('/')}>Go back</button>
    </div>
  {:else if agent}
    <div class="agent-header">
      <div class="agent-icon-large">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
      </div>
      <div class="agent-header-info">
        <h1>{agent.name}</h1>
        <p class="agent-description">{agent.description}</p>
        <div class="agent-badges">
          <span class="badge model-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            </svg>
            {agent.llm_model}
          </span>
          <span class="badge provider-badge">{agent.llm_provider}</span>
        </div>
      </div>
    </div>

    <div class="prompts-section">
      <h2>Example Prompts</h2>
      <p class="prompts-subtitle">Click on any prompt to start a conversation with this agent</p>

      <div class="prompts-grid">
        {#each agent.prompts as prompt}
          <button
            class="prompt-card"
            on:click={() => startChatWithPrompt(prompt.content)}
          >
            <div class="prompt-card-header">
              <h3>{prompt.title}</h3>
              <svg class="prompt-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </div>
            <p class="prompt-content">{prompt.content}</p>
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .agent-detail {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 24px;
  }

  .loading-container, .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    text-align: center;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid var(--border-color, #e5e5e5);
    border-top-color: var(--primary-color, #667eea);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .agent-header {
    display: flex;
    gap: 24px;
    margin-bottom: 48px;
    padding-bottom: 32px;
    border-bottom: 1px solid var(--border-color, #e5e5e5);
  }

  .agent-icon-large {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    color: white;
    flex-shrink: 0;
  }

  .agent-header-info {
    flex: 1;
  }

  .agent-header-info h1 {
    font-size: 32px;
    font-weight: 700;
    margin: 0 0 12px 0;
    color: var(--text-primary, #202123);
  }

  .agent-description {
    font-size: 16px;
    color: var(--text-secondary, #6e6e80);
    margin: 0 0 16px 0;
    line-height: 1.5;
  }

  .agent-badges {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
  }

  .model-badge {
    background: #f0f4ff;
    color: #4f46e5;
  }

  .provider-badge {
    background: #f3f4f6;
    color: #6b7280;
  }

  .prompts-section h2 {
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: var(--text-primary, #202123);
  }

  .prompts-subtitle {
    font-size: 14px;
    color: var(--text-secondary, #6e6e80);
    margin: 0 0 24px 0;
  }

  .prompts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }

  .prompt-card {
    background: white;
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: 12px;
    padding: 20px;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
  }

  .prompt-card:hover {
    border-color: var(--primary-color, #667eea);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    transform: translateY(-2px);
  }

  .prompt-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .prompt-card-header h3 {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
    color: var(--text-primary, #202123);
    flex: 1;
  }

  .prompt-arrow {
    color: var(--text-secondary, #6e6e80);
    transition: transform 0.2s;
    flex-shrink: 0;
  }

  .prompt-card:hover .prompt-arrow {
    transform: translateX(4px);
    color: var(--primary-color, #667eea);
  }

  .prompt-content {
    font-size: 14px;
    color: var(--text-secondary, #6e6e80);
    line-height: 1.5;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .error-container h2 {
    color: var(--error-color, #ef4444);
    margin-bottom: 16px;
  }

  .error-container button {
    padding: 12px 24px;
    background: var(--primary-color, #667eea);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    margin-top: 16px;
  }

  .error-container button:hover {
    background: var(--primary-hover, #5568d3);
  }
</style>
