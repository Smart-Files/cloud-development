<script lang="ts">
	import ChatList from '$lib/components/ChatList.svelte';
	import ChatPanel from '$lib/components/ChatPanel.svelte';
	import EmptyScreen from '$lib/components/EmptyScreen.svelte';
	import ChatLoading from '$lib/components/ChatLoading.svelte';
	import { cn } from '$lib/utils';
	import { onMount } from 'svelte';
	import { usePosts } from '../../stores/posts';
	import { input, write_status } from '../../stores/store';
	import { WriteStatus } from '../../stores/types';

	// TODO: Save in local storage
	let previewToken: string | null = null;
	let className: string | undefined | null = undefined;
	export { className as class };

	let posts: ReturnType<typeof usePosts>;

	onMount(() => {
		posts = usePosts();
		posts.authenticate().then(() => {
			write_status.set(WriteStatus.IDLE);
			posts.createChat(); // Create a new chat
		});
	});
</script>

<div class={cn('pb-[200px] pt-4 md:pt-10', className)}>
	{#if $write_status === WriteStatus.DONE}
		<ChatList />
	{:else if $write_status === WriteStatus.LOADING}
		<ChatLoading />
	{:else}
		<ChatList />
		<EmptyScreen {input} />
	{/if}
</div>

<ChatPanel {input} />
