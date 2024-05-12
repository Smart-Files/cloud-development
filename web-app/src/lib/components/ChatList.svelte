<script lang="ts">
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import { Separator } from '$lib/components/ui/separator';
	import type { UseChatHelpers } from 'ai/svelte';
	import type { Readable, Writable } from 'svelte/store';
	import type { Post, PostStore, usePosts } from '../../stores/posts';

	export let posts: ReturnType<typeof usePosts>;
	let uuid: string;
	let messages: Post[];

	$: {
		if ($posts) {
			uuid = posts.getUUID();
			messages = $posts.chats[uuid];
		}
	}
</script>

{#if $posts.chats}
	<div class="relative mx-auto max-w-2xl px-4">
		{#each messages as message, index}
			<div>
				<ChatMessage {message} />
				{#if index < messages.length - 1}
					<Separator class="my-4 md:my-8" />
				{/if}
			</div>
		{/each}
	</div>
{/if}
