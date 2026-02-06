<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { user, models } from '$lib/stores';
	import { getAgentById } from '$lib/apis/agents';
	import AgentIcon from '$lib/components/icons/Agent.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let loading = true;
	let agent = null;

	onMount(async () => {
		const agentId = $page.params.id;
		try {
			agent = await getAgentById(localStorage.token, $user?.email, agentId);
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});

	const startChat = (promptValue = '') => {
		if (!agent) return;

		const params = new URLSearchParams();
		params.set('model', agent.id);
		if (promptValue) {
			params.set('q', promptValue);
		}

		goto(`/?${params.toString()}`);
	};
</script>

<svelte:head>
	<title>{agent ? `${agent.name} | Agentes` : 'Agente | Agentes'}</title>
</svelte:head>

<div class="flex flex-col h-full overflow-y-auto w-full dark:bg-gray-900 dark:text-gray-100">
	<div class="max-w-4xl mx-auto w-full px-4 py-8">
		<div class="mb-6">
			<button
				on:click={() => goto('/agents')}
				class="flex items-center text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 20 20"
					fill="currentColor"
					class="size-4 mr-1"
				>
					<path
						fill-rule="evenodd"
						d="M17 10a.75.75 0 0 1-.75.75H5.612l4.158 3.96a.75.75 0 1 1-1.04 1.08l-5.5-5.25a.75.75 0 0 1 0-1.08l5.5-5.25a.75.75 0 1 1 1.04 1.08L5.612 9.25H16.25A.75.75 0 0 1 17 10Z"
						clip-rule="evenodd"
					/>
				</svg>
				Voltar para Agentes
			</button>
		</div>

		{#if loading}
			<div class="flex justify-center items-center h-64">
				<Spinner />
			</div>
		{:else if !agent}
			<div class="flex flex-col items-center justify-center h-64 text-gray-500">
				<p>Agente não encontrado.</p>
			</div>
		{:else}
			<div
				class="bg-white dark:bg-gray-850 rounded-3xl p-8 border border-gray-100 dark:border-gray-800 shadow-sm mb-8"
			>
				<div
					class="flex flex-col md:flex-row items-center md:items-start text-center md:text-left gap-6"
				>
					<div class="p-6 rounded-3xl bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
						<AgentIcon className="size-16" />
					</div>
					<div class="flex-1">
						<h1 class="text-3xl font-bold mb-2">{agent.name}</h1>
						<div class="flex flex-wrap items-center justify-center md:justify-start gap-3 mb-4">
							<div class="flex items-center gap-1.5">
								<span class="text-xs text-gray-400 font-medium uppercase tracking-tight"
									>Provedor:</span
								>
								<span
									class="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 uppercase tracking-wider"
								>
									{agent.llm_provider}
								</span>
							</div>
							<div class="flex items-center gap-1.5">
								<span class="text-xs text-gray-400 font-medium uppercase tracking-tight"
									>Modelo:</span
								>
								<span
									class="text-xs font-semibold px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 uppercase tracking-wider"
								>
									{agent.llm_model}
								</span>
							</div>
						</div>
						<p class="text-gray-600 dark:text-gray-400 leading-relaxed max-w-2xl">
							{agent.description}
						</p>
					</div>
				</div>

				<div class="mt-8 flex justify-center md:justify-start">
					<button
						on:click={() => startChat()}
						class="px-6 py-3 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-full font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors shadow-lg"
					>
						Iniciar Chat com Agente
					</button>
				</div>
			</div>

			{#if agent.prompts && agent.prompts.length > 0}
				<div>
					<h2 class="text-xl font-semibold mb-6 px-2">Prompts Sugeridos</h2>
					<div class="grid grid-cols-1 gap-4">
						{#each agent.prompts as prompt}
							<button
								on:click={() => startChat(prompt.content)}
								class="flex items-center justify-between p-6 rounded-2xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-850 hover:border-blue-300 dark:hover:border-blue-700 hover:shadow-md transition-all group text-left w-full"
							>
								<div class="flex-1">
									<h3
										class="font-semibold text-lg mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
									>
										{prompt.title}
									</h3>
									<p class="text-gray-500 dark:text-gray-400 text-sm line-clamp-1">
										{prompt.content}
									</p>
								</div>
								<div
									class="ml-4 p-2 rounded-full bg-gray-50 dark:bg-gray-800 text-gray-400 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 group-hover:text-blue-600 transition-all"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										viewBox="0 0 20 20"
										fill="currentColor"
										class="size-5"
									>
										<path
											fill-rule="evenodd"
											d="M3 10a.75.75 0 0 1 .75-.75h10.638L10.23 5.29a.75.75 0 1 1 1.04-1.08l5.5 5.25a.75.75 0 0 1 0 1.08l-5.5 5.25a.75.75 0 1 1-1.04-1.08l4.158-3.96H3.75A.75.75 0 0 1 3 10Z"
											clip-rule="evenodd"
										/>
									</svg>
								</div>
							</button>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>
