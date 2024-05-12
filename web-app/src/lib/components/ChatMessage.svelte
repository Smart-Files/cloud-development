<script lang="ts">
	import ChatMessageActions from '$lib/components/ChatMessageActions.svelte';
	import { IconOpenAI, IconUser } from '$lib/components/ui/icons';
	import { cn } from '$lib/utils';
	import type { Message } from 'ai';
	import type { Post } from '../../stores/posts';
	import IconSvelteChat from './ui/icons/IconSvelteChat.svelte';
	import { Card } from 'flowbite-svelte';
	import { CodeBlock } from 'svhighlight';

	export let message: Post;

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
			return { language: 'plaintext', headerText: tool };
		}
	}

	function formatMessage(message: string) {
		// let content = message.replace("\n", "</br>")
		let content = message
			.split('\n')
			.map((line) => {
				if (line.startsWith('Action: ') || line.startsWith('Action Input: ')) {
					return '';
				}

				if (line.startsWith('Command: ')) {
					return '';
				}
				return line;
			})
			.join('<br/>');

		return content;
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
		{@html formatMessage(message.content)}
		{#if message.actions}
			{#each message.actions as action}
				{console.log(action)}
				<CodeBlock
					code={action.tool_input.replace('/', '&#92;')}
					language={getSearchType(action.tool).language}
					headerText={getSearchType(action.tool).headerText}
					showLineNumbers={false}
				/>
			{/each}
		{/if}
		{#if message.output && message.files}
			{#each message.files as file}
				<a target="_blank" href={`/download/${file}?uuid=${message.uuid}`}>
					<div
						class="max-w-sm p-6 bg-white border border-gray-200 rounded-lg shadow dark:bg-gray-800 dark:border-gray-700"
					>
						<h5 class="mb-2 text-lg font-semibold tracking-tight text-gray-900 dark:text-white">
							{truncate(file, 20)}
						</h5>
						<p class="mb-3 font-normal text-gray-500 dark:text-gray-400">Click to download</p>
					</div>
				</a>
			{/each}
		{/if}
	</div>

	<ChatMessageActions {message} />
</div>
