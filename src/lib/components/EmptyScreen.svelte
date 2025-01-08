<script lang="ts">
	import ExternalLink from '$lib/components/ExternalLink.svelte';
	import { Button } from '$lib/components/ui/button';
	import { IconArrowRight } from '$lib/components/ui/icons';
	import type { UseChatHelpers } from 'ai/svelte';

	export let input: UseChatHelpers['input'];

	const exampleMessages = [
		{
			heading: 'Convert a PNG file to JPG',
			message: `Convert this PNG file to JPG`
		},
		{
			heading: 'Extract audio from a video',
			message: 'Extract the audio from this video and save as an mp3 file'
		},
		{
			heading: 'Convert a PDF to a Word document',
			message: `Convert this PDF to a Word document`
		}
	];
</script>

<div class="mx-auto max-w-2xl px-4">
	<div class="rounded-lg border bg-background p-8">
		<h1 class="mb-2 text-lg font-semibold">Welcome to SmartFile AI Chatbot!</h1>
		<p class="mb-2 leading-normal text-muted-foreground">
			This is an AI file converter app built with
			<ExternalLink href="https://kit.svelte.dev">SvelteKit</ExternalLink>
			.
		</p>
		<p class="leading-normal text-muted-foreground">
			You can start a conversation here or try the following examples:
		</p>
		<div class="mt-4 flex flex-col items-start space-y-2">
			{#each exampleMessages as message}
				<Button
					variant="link"
					class="h-auto p-0 text-base"
					on:click={() => ($input = message.message)}
				>
					<IconArrowRight class="mr-2 text-muted-foreground" />
					{message.heading}
				</Button>
			{/each}
		</div>
	</div>
</div>
