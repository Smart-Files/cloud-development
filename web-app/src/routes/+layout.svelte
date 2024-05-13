<script lang="ts">
	import Header from '$lib/components/Header.svelte';

	import { resolvedTheme } from '$lib/theme';
	import '@fontsource/inter';
	import '@fontsource/jetbrains-mono';
	import '../app.postcss';
	import type { LayoutServerData } from './$types';
	import { onDestroy } from 'svelte';
</script>

<svelte:head>
	<title>SmartFile -- Chat</title>
</svelte:head>

<Header />
<main class="flex flex-col flex-1 bg-muted/50">
	<slot />
</main>
