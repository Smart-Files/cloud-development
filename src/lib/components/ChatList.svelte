<script lang="ts">
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import { Separator } from '$lib/components/ui/separator';
	import { get, type Readable, type Writable } from 'svelte/store';
	import { usePosts } from '../../stores/posts';
	import FileBlock from './FileBlock.svelte';
	import { onMount } from 'svelte';
	import { WriteStatus, type Post, type UploadFile } from '../../stores/types';
	import { files, write_status } from '../../stores/store';

	let posts: ReturnType<typeof usePosts>;
	let uuid: string;
	let messages: Post[];

	onMount(() => {
		posts = usePosts();

		posts.subscribe((chatData) => {
			uuid = posts.getUUID();
			if (chatData && chatData.posts) {
				messages = chatData.posts;
			}
		});
	});

	function handleFileDelete(event: CustomEvent) {
		const deletedFile: UploadFile = event.detail.uploadFile;
		get(write_status);

		if (get(write_status) === WriteStatus.LOADING) {
			return;
		}

		posts.deleteFile(deletedFile.uuid);
	}

	$: fileData = Object.values($files);
</script>

{#if $files}
	<div class="relative mx-auto max-w-2xl px-4">
		<!-- Uploaded Files -->
		<div
			class="flex flex-wrap max-h-36 overflow-y-scroll gap-2 mb-6 justify-items-start content-around"
		>
			{#each fileData as file, index}
				<div
					class="flex-grow sm:flex-grow-0 sm:basis-1/{$files.length} min-w-[220px] basis-[calc(50% - 1rem)] max-w-[100%]"
				>
					<FileBlock uploadFile={file} on:delete={handleFileDelete} />
				</div>
			{/each}
		</div>
		{#if messages}
			{#each messages as message, index}
				<div>
					<ChatMessage {message} />
					{#if index < messages.length - 1}
						<Separator class="my-4 md:my-8" />
					{/if}
				</div>
			{/each}
			{#if messages.length >= 3}
				<div class="h-28"></div>
			{/if}
		{/if}
	</div>
{/if}
