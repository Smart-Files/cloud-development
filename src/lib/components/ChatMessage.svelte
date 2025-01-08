<script lang="ts">
	import ChatMessageActions from '$lib/components/ChatMessageActions.svelte';
	import { IconDownload, IconOpenAI, IconUser } from '$lib/components/ui/icons';
	import { cn } from '$lib/utils';
	import type { Message } from 'ai';
	import type { Post } from '../../stores/typ';
	import IconSvelteChat from './ui/icons/IconSvelteChat.svelte';
	import { Card } from 'flowbite-svelte';
	import { CodeBlock } from 'svhighlight';
	import { BASE_URL } from '$lib/constants';
	import { onMount } from 'svelte';
	import type { AnyNode } from 'postcss';

	export let message: Post;

	onMount(() => {
		console.log('CHANGE', message);
	});

	function truncate(text: string, totalChars: number, endChars = 0) {
		endChars = Math.min(endChars, totalChars);
		const start = text.slice(0, totalChars - endChars);
		const end = endChars > 0 ? text.slice(-endChars) : '';

		if (start.length + end.length < text.length) {
			return start + '…' + end;
		} else {
			return text;
		}
	}

	function getSearchType(tool: string) {
		// Implement the logic to determine the language and headerText based on the tool
		// For example:
		let tool_name = tool.toLowerCase();
		if (tool_name.includes('shell')) {
			return { language: 'bash', headerText: 'Executing Shell Command' };
		} else if (tool_name.includes('search')) {
			return { language: 'plaintext', headerText: 'Searching Documentation' };
		} else {
			let titleCased = tool
				.replace('_', ' ')
				.replace(
					/\w\S*/g,
					(text) => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase()
				);

			return { language: 'plaintext', headerText: titleCased };
		}
	}

	function formatMessage(messages: any[]): string {
		// let content = message.replace("\n", "</br>")
		let content = messages
			.map((el) => el.content)
			.join('')
			.trim();

		if (content.startsWith('```json') && content.endsWith('```')) {
			content = content.replace('```json', '').replace('```', '').trim();

			let parsed_content;

			try {
				parsed_content = JSON.parse(content);
			} catch (e) {
				console.log('Error parsing content', e, '\n\nContent:', content);

				return content;
			}

			let message_action = parsed_content['action'];
			let action_input = parsed_content['action_input'] ?? '';

			if (message_action) {
				switch (message_action) {
					case 'execute_command':
						return '';
					case 'search_file_tools_docs':
						const content_text = ` for &quot;<span class="text-zinc-400 italic">${action_input}</span>&quot;`;
						return `Let me search my documentation${action_input ? content_text : '.'}`;
					case 'Final Answer':
						return action_input;
				}
			}
		}

		return content;
	}

	function process_input(input: string) {
		if (input.startsWith('```') && input.endsWith('```')) {
			return input.slice(3, -3);
		}
		if (input.startsWith('`') && input.endsWith('`')) {
			return input.slice(1, -1);
		}

		return input;
	}

	function process_output(output: string) {
		let result = '';
		let stdout = output.match(/STDOUT:((.|\n)*)STDERR/s);
		let stderr = output.match(/STDERR:((.|\n)*)Return Code/s);
		if (stdout) {
			result = stdout[1] + '\n';
		}
		if (stderr) {
			result += stderr[1] + '\n';
		}

		// Remove surrounding backticks if they wrap the output
		if (result.startsWith('`') && result.endsWith('`')) {
			result = result.slice(1, -1);
		}

		result = result.replaceAll('None', '').trim();

		if (result.length > 1000) {
			result = result.substring(0, 996) + '...';
		}
		return result;
	}
</script>

<div class={cn('group relative mb-4 flex items-start md:-ml-12')} {...$$restProps}>
	<div
		class={cn(
			'flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md border shadow',
			message.role === 'user' ? 'bg-background' : 'bg-primary text-primary-foreground'
		)}
	>
		{#if message.role === 'user'}
			<IconUser />
		{:else}
			<IconSvelteChat />
		{/if}
	</div>
	<div class="ml-4 flex-1 space-y-2 overflow-hidden px-1">
		{@html formatMessage(message.messages)}
		{#if message.actions}
			{#each message.actions as action}
				<CodeBlock
					code={process_input(action.tool_input)}
					language={getSearchType(action.tool).language}
					headerText={getSearchType(action.tool).headerText}
					showLineNumbers={false}
				/>
				{#if message.output}
					{#if process_output(message.output).length > 0}
						<div
							class="text-stone-300 bg-slate-950 p-2 rounded-md font-mono text-sm overflow-x-auto overflow-y-auto"
						>
							{process_output(message.output)}
						</div>
					{:else}
						<div
							class="text-stone-600 bg-slate-950 italic p-2 rounded-md font-mono text-sm overflow-x-auto overflow-y-auto"
						>
							No output
						</div>
					{/if}
				{/if}
			{/each}
		{/if}
		{#if message.output && message.files}
			<!-- Separator -->
			<!-- <div class="h-4 w-4 bg-gray-2000 rounded-full"></div> -->
			<div class="w-full rounded-md mt-5 flex flex-row flex-wrap gap-3">
				{#each message.files as file}
					<a target="_blank" href={`${BASE_URL}download/${message.uuid}/${file}`}>
						<div
							class="flex flex-row justify-center pl-4 pr-2 py-1 w-30 h-30 bg-white border border-gray-200 rounded-lg shadow dark:bg-gray-800 dark:border-gray-700"
						>
							<h5
								class="flex-nowrap m-auto mx-auto my-auto text-nowrap leading-9 text-sm font-semibold tracking-tight text-gray-900 dark:text-white"
							>
								{truncate(file, 40)}
							</h5>
							<IconDownload class="w-6 h-6 my-2 mx-2" />
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</div>

	<ChatMessageActions {message} />
</div>
