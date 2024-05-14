<script lang="ts">
	import ChatList from '$lib/components/ChatList.svelte';
	import ChatPanel from '$lib/components/ChatPanel.svelte';
	import EmptyScreen from '$lib/components/EmptyScreen.svelte';
	import { cn } from '$lib/utils';
	import { onMount } from 'svelte';
	import { usePosts, input } from '../../stores/posts';

	// TODO: Save in local storage
	let previewToken: string | null = null;
	let className: string | undefined | null = undefined;
	export { className as class };

	let posts: ReturnType<typeof usePosts>;

	onMount(() => {
		posts = usePosts();
	});
</script>

<div class={cn('pb-[200px] pt-4 md:pt-10', className)}>
	{#if $posts}
		<ChatList {posts} />
	{:else}
		<EmptyScreen {input} />
	{/if}
</div>

<ChatPanel {posts} {input} />
