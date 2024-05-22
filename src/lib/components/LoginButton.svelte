<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { IconGitHub, IconSpinner } from '$lib/components/ui/icons';
	import { cn } from '$lib/utils';
	import type { Writable } from 'svelte/store';
	import { WriteStatus } from '../../stores/posts';

	export let text = 'Login with GitHub';
	export let showGithubIcon = true;

	let className: string | undefined | null = undefined;
	export { className as class };

	export let isLoading: Writable<WriteStatus>;
</script>

<Button
	variant="outline"
	on:click={() => {
		// isLoading.set(true);
		// signIn('github', { callbackUrl: `/` });
	}}
	disabled={$isLoading === WriteStatus.LOADING || $isLoading === WriteStatus.error}
	class={cn(className)}
	{...$$restProps}
>
	{#if $isLoading === WriteStatus.LOADING}
		<IconSpinner class="mr-2 animate-spin" />
	{:else if showGithubIcon}
		<IconGitHub class="mr-2" />
	{/if}
	{text}
</Button>
