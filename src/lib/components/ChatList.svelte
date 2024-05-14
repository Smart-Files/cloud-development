<script lang="ts">
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import { Separator } from '$lib/components/ui/separator';
	import type { UseChatHelpers } from 'ai/svelte';
	import { get, type Readable, type Writable } from 'svelte/store';
	import type { Post, PostStore, usePosts } from '../../stores/posts';
	import { WriteStatus, files } from '../../stores/posts';
	import FileBlock from './FileBlock.svelte';
	import { write_status } from '../../stores/posts';

	export let posts: ReturnType<typeof usePosts>;
	let uuid: string;
	let messages: Post[];

	posts.subscribe((val) => {
		uuid = posts.getUUID();
		messages = val.chats?.[uuid];
	});

	function handleFileDelete(event: CustomEvent) {
		const deletedFile = event.detail.file;
		get(write_status);

		if (get(write_status) === WriteStatus.LOADING) {
			return;
		}

		posts.deleteFile(deletedFile);
	}
</script>

{#if $posts.chats}
	<div class="relative mx-auto max-w-2xl px-4">
		<!-- Uploaded Files -->
		{#if $files}
			<div
				class="flex flex-wrap max-h-36 overflow-y-scroll gap-2 mb-6 justify-items-start content-around"
			>
				{#each $files as file, index}
					<div
						class="flex-grow sm:flex-grow-0 sm:basis-1/{$files.length} min-w-[220px] basis-[calc(50% - 1rem)] max-w-[100%]"
					>
						<FileBlock {file} on:delete={handleFileDelete} />
					</div>
				{/each}
			</div>
		{/if}
		{#if messages}
			{#each messages as message, index}
				<div>
					<ChatMessage {message} />
					{#if index < messages.length - 1}
						<Separator class="my-4 md:my-8" />
					{/if}
				</div>
			{/each}
		{/if}
	</div>
{/if}
