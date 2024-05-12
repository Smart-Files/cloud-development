<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { IconArrowElbow, IconPlus } from '$lib/components/ui/icons';
	import { Tooltip, TooltipContent, TooltipTrigger } from '$lib/components/ui/tooltip';
	import type { UseChatHelpers } from 'ai/svelte';
	import { createEventDispatcher, onMount } from 'svelte';
	// @ts-ignore
	import autosize from 'svelte-autosize';
	import {
		Fileupload,
		Label,
		Listgroup,
		ListgroupItem,
		Dropzone,
		Indicator
	} from 'flowbite-svelte';
	import { get, writable } from 'svelte/store';
	import type { ChangeEvent } from 'svelte/elements';
	import { FileSymlink } from 'lucide-svelte';
	import { files, input } from '../../stores/posts';

	// All files that are uploaded will be stored here
	let draggingOver = false; // Whether the user is dragging over the dropzone or not

	const dispatch = createEventDispatcher<{ submit: { input: string; files: File[] } }>();

	const draggingOverClass =
		'flex flex-row justify-center items-center w-full rounded-lg border-2 border-dashed outline-4 outline outline-zinc-900 cursor-pointer bg-zinc-900 border-dashed border-blue-700 opacity-80 h-16'; // Classes to apply when the user is dragging over the dropzone
	const notDraggingOverClass =
		'flex flex-row justify-center items-center w-full rounded-lg border-2 outline-4 outline outline-zinc-900 hover:outline-zinc-800 hover:border-zinc-8000 cursor-pointer bg-zinc-900 border-zinc-900 hover:bg-zinc-800 h-16'; // Classes to apply when the user is not dragging over the dropzone

	export let isLoading: UseChatHelpers['isLoading'];
	// export let files: UseChatHelpers['files'];

	async function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			await dispatch('submit', { input: $input, files: get(files) });
			$input = '';
			$files = [];
		}
	}

	const dragOver = (e: DragEvent) => {
		draggingOver = true;
	};

	const dragLeave = () => {
		draggingOver = false;
	};

	const dropHandle = (event: DragEvent) => {
		draggingOver = false;
		event.preventDefault();
		if (event.dataTransfer?.items) {
			[...event.dataTransfer.items].forEach((item, i) => {
				console.log('ITEM', item);
				let file: File;
				if (item.kind === 'file' && (file = item.getAsFile()) !== null) {
					files.update((files) => [...files, file]);
				} else {
					console.log('ERROR: NOT A FILE');
				}
			});
		} else {
			[...event.dataTransfer?.files].forEach((file, i) => {
				console.log('FILE', file);
				files.update((files) => [...files, file]);
			});
		}
	};

	const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
		const eventFiles = event.target.files;
		for (const file of eventFiles) {
			files.update((files) => [...files, file]);
		}
	};

	const showFiles = (files: File[]) => {
		if (files.length === 1) return files[0];
		let concat = '';
		files.map((file: File) => {
			concat += file;
			concat += ',';
			concat += ' ';
		});

		if (concat.length > 40) concat = concat.slice(0, 40);
		concat += '...';
		return concat;
	};
</script>

<div class="flex flex-col p-2 pt-3">
	<Dropzone
		id="dropzone"
		multiple
		defaultClass={`${draggingOver ? draggingOverClass : notDraggingOverClass}`}
		{$files}
		on:drop={dropHandle}
		on:dragover={(event) => {
			event.preventDefault();
		}}
		on:dragenter={dragOver}
		on:dragleave={dragLeave}
		on:change={handleChange}
	>
		<div class="flex flex-col items-center justify-center px-6">
			<p class="mb-2 text-sm text-gray-500 dark:text-gray-400">
				<span class="font-semibold">Click to upload</span> or drag and drop
			</p>
			<p class="text-xs text-gray-500 dark:text-gray-400">
				SVG, PNG, JPG, GIF, PDF, DOCX, XLSX, CSV, HTML, etc.
			</p>
		</div>
		<svg
			aria-hidden="true"
			class="w-10 h-10 text-gray-400"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
			/>
		</svg>
	</Dropzone>
	{#if $files}
		<div>
			{#each $files as file}
				<span class="flex items-center">
					<Indicator size="sm" color="orange" class="me-1.5" />
					{file.name}
				</span>
			{/each}
		</div>
	{/if}
</div>
<form
	on:submit={async (event) => {
		event.preventDefault();
		if ($input === '') {
			return;
		}
		await dispatch('submit', { input: get(input), files: get(files) });
		$input = '';
	}}
	class="flex flex-col"
>
	<div
		class="relative flex w-full grow flex-col overflow-hidden bg-background sm:rounded-md sm:border"
	>
		<Tooltip>
			<TooltipTrigger>
				<Button
					href="/"
					target="_self"
					size="sm"
					variant="outline"
					class="absolute left-0 top-4 h-8 w-8 rounded-full bg-background p-0 sm:left-4"
				>
					<IconPlus />
					<span class="sr-only">New Chat</span>
				</Button>
			</TooltipTrigger>
			<TooltipContent>New Chat</TooltipContent>
		</Tooltip>
		{#if $input !== undefined}
			<textarea
				use:autosize
				autofocus={true}
				tabindex={0}
				on:keydown={handleKeydown}
				rows={1}
				bind:value={$input}
				placeholder="Send a message."
				spellcheck={false}
				class="min-h-[60px] pl-16 w-full resize-none bg-transparent px-4 py-[1.3rem] focus:shadow-none focus-within:outline-none sm:text-sm border-none outline-none focus:border-none focus:outline-none"
			/>
		{/if}
		<div class="absolute right-0 top-3 sm:right-4">
			<Tooltip>
				<TooltipTrigger>
					<Button type="submit" size="icon" disabled={$isLoading || $input === ''}>
						<IconArrowElbow />
						<span class="sr-only">Send message</span>
					</Button>
				</TooltipTrigger>
				<TooltipContent>Send message</TooltipContent>
			</Tooltip>
		</div>
	</div>
</form>
