<script lang="ts">
	import { IconDownload, IconTrash } from '$lib/components/ui/icons';
	import { createEventDispatcher } from 'svelte';
	import type { UploadFile } from '../../stores/posts';

	export let uploadFile: UploadFile;

	const dispatch = createEventDispatcher();

	function handleDelete() {
		dispatch('delete', { uploadFile });
	}
</script>

<div class="bg-zinc-800 rounded-lg p-4 flex items-center justify-between">
	<div class="flex items-center">
		<button
			on:click={handleDelete}
			class="text-zinc-200 hover:text-red-400 transition-colors duration-200 mr-4"
		>
			<IconTrash class="w-5 h-5" />
		</button>
		<div>
			<p class="text-sm font-medium text-zinc-200">{uploadFile.name}</p>
			<p class="text-xs text-zinc-400">{(uploadFile.file.size / 1024).toFixed(2)} KB</p>
		</div>
	</div>
	<a
		href={URL.createObjectURL(uploadFile.file)}
		download={uploadFile.name}
		class="text-blue-500 hover:text-blue-600 transition-colors duration-200"
	>
		<IconDownload class="w-5 h-5 ml-3" />
	</a>
</div>
