<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';
	import { getAgents } from '$lib/apis/agents';
	import AgentIcon from '$lib/components/icons/Agent.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let loading = true;
	let agents = [];

	onMount(async () => {
		try {
			agents = await getAgents(localStorage.token, $user?.email);
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col h-full overflow-y-auto w-full dark:bg-gray-900 dark:text-gray-100">
	<div class="max-w-6xl mx-auto w-full px-4 py-8">
		<div class="mb-8">
			<h1 class="text-3xl font-semibold mb-2">Agentes</h1>
			<p class="text-gray-500 dark:text-gray-400">
				Selecione um agente para iniciar uma conversa especializada.
			</p>
		</div>

		{#if loading}
			<div class="flex justify-center items-center h-64">
				<Spinner />
			</div>
		{:else if agents.length === 0}
			<div class="flex flex-col items-center justify-center h-64 text-gray-500">
				<AgentIcon className="size-12 mb-4 opacity-20" />
				<p>Nenhum agente encontrado.</p>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				{#each agents as agent}
					<a
						href="/agents/{agent.id}"
						class="flex flex-col p-6 rounded-2xl border border-gray-100 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 transition-all group bg-white dark:bg-gray-850 shadow-sm hover:shadow-md"
					>
						<div class="flex items-center mb-4">
							<div
								class="p-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 group-hover:bg-blue-50 dark:group-hover:bg-blue-900/30 group-hover:text-blue-600 transition-colors"
							>
								<AgentIcon className="size-6" />
							</div>
							<div class="ml-4 flex-1">
								<h2 class="font-semibold text-lg line-clamp-1">{agent.name}</h2>
								<div class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wider">
									{agent.llm_provider} • {agent.llm_model}
								</div>
							</div>
						</div>
						<p class="text-gray-600 dark:text-gray-400 text-sm line-clamp-2 mb-4 flex-1">
							{agent.description}
						</p>
						<div
							class="flex items-center justify-between mt-auto pt-4 border-t border-gray-50 dark:border-gray-800"
						>
							<span
								class="text-xs font-medium px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
							>
								{agent.prompt_count}
								{agent.prompt_count === 1 ? 'sugestão' : 'sugestões'}
							</span>
							<span
								class="text-blue-600 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity"
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
							</span>
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</div>
</div>
