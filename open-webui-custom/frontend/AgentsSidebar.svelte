<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  let agents = [];
  let loading = true;
  let error = null;

  async function fetchAgents() {
    try {
      const response = await fetch('/api/agents', {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        agents = data.agents || [];
      } else {
        error = 'Failed to load agents';
      }
    } catch (e) {
      console.error('Error fetching agents:', e);
      error = 'Error loading agents';
    } finally {
      loading = false;
    }
  }

  function openAgent(agentId) {
    goto(`/agents/${agentId}`);
  }

  onMount(() => {
    fetchAgents();
  });
</script>

<div class="agents-sidebar">
  <div class="sidebar-header">
    <h3>
      <svg class="icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
      </svg>
      AI Agents
    </h3>
  </div>

  <div class="agents-list">
    {#if loading}
      <div class="loading">
        <div class="spinner"></div>
        <span>Loading agents...</span>
      </div>
    {:else if error}
      <div class="error">
        <span>{error}</span>
      </div>
    {:else if agents.length === 0}
      <div class="empty">
        <span>No agents available</span>
      </div>
    {:else}
      {#each agents as agent}
        <button
          class="agent-item"
          on:click={() => openAgent(agent.id)}
        >
          <div class="agent-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div class="agent-info">
            <div class="agent-name">{agent.name}</div>
            <div class="agent-meta">
              <span class="agent-model">{agent.llm_model}</span>
              {#if agent.prompt_count > 0}
                <span class="prompt-count">{agent.prompt_count} prompts</span>
              {/if}
            </div>
          </div>
        </button>
      {/each}
    {/if}
  </div>
</div>

<style>
  .agents-sidebar {
    width: 260px;
    height: 100%;
    background: var(--sidebar-bg, #f7f7f8);
    border-right: 1px solid var(--border-color, #e5e5e5);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid var(--border-color, #e5e5e5);
  }

  .sidebar-header h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary, #202123);
  }

  .icon {
    flex-shrink: 0;
  }

  .agents-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .agent-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    margin-bottom: 4px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }

  .agent-item:hover {
    background: var(--hover-bg, #ececf1);
    border-color: var(--border-color, #d9d9e3);
  }

  .agent-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 8px;
    color: white;
    flex-shrink: 0;
  }

  .agent-info {
    flex: 1;
    min-width: 0;
  }

  .agent-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary, #202123);
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .agent-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-secondary, #6e6e80);
  }

  .agent-model {
    padding: 2px 6px;
    background: var(--tag-bg, #e5e5ea);
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
  }

  .prompt-count {
    font-size: 11px;
  }

  .loading, .error, .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 16px;
    text-align: center;
    color: var(--text-secondary, #6e6e80);
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color, #e5e5e5);
    border-top-color: var(--primary-color, #667eea);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 12px;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .error {
    color: var(--error-color, #ef4444);
  }
</style>
