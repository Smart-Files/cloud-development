<script lang="ts">
	import ButtonScrollToBottom from '$lib/components/ButtonScrollToBottom.svelte';
	import { Button } from '$lib/components/ui/button';
	import { IconRefresh, IconStop } from '$lib/components/ui/icons';
	import FooterText from '$lib/components/FooterText.svelte';
	import PromptForm from '$lib/components/PromptForm.svelte';
	import type { Writable } from 'svelte/store';
	import { usePosts } from '../../stores/posts';
	import { onMount } from 'svelte';
	import { WriteStatus, type Post, type UploadFile } from '../../stores/types';
	import { write_status } from '../../stores/store';

	let id: string;
	let messages: Post[];

	let posts: ReturnType<typeof usePosts>;

	onMount(() => {
		posts = usePosts();
	});

	$: {
		if ($posts) {
			id = posts.getUUID();
			messages = $posts.posts;
		}
	}

	const stop = () => {
		// posts.stop();
		posts.stop();
	};
	const reload = () => {
		// posts.reload();
	};

	const gen = ({ input }: { input: string }) => {
		console.log('input', input);
		posts.generate(input);
	};
</script>

<div class="fixed inset-x-0 bottom-0 bg-gradient-to-b from-muted/10 from-10% to-muted/30 to-50%">
	<ButtonScrollToBottom />
	<div class="mx-auto sm:max-w-2xl sm:px-4">
		<div class="flex h-10 items-center justify-center">
			{#if $write_status == WriteStatus.LOADING}
				<Button variant="outline" on:click={() => stop()} class="bg-background">
					<IconStop class="mr-2" />
					Stop generating
				</Button>
			{:else if $posts && $posts.posts.length > 0}
				<Button variant="outline" on:click={() => reload()} class="bg-background">
					<IconRefresh class="mr-2" />
					Regenerate response
				</Button>
			{/if}
		</div>
		<div
			class="space-y-4 border-t bg-background px-4 py-2 shadow-lg sm:rounded-t-xl sm:border md:py-4"
		>
			<PromptForm
				on:submit={async (event) => {
					gen(event.detail);
				}}
				writeStatus={write_status}
			/>
		</div>
	</div>
</div>
