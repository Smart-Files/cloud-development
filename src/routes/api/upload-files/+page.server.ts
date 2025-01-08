import { fail } from '@sveltejs/kit';
import { BASE_URL } from "$lib/constants.js"

// Upload Files for chat session
/** @type {import('./$types').Actions} */
export const actions = {
    default: async ({ request }) => {
        const formData = Object.fromEntries(await request.formData());

        if (
            !(formData.uuid as string) ||
            (formData.uuid as string) === 'undefined'
        ) {
            return fail(400, {
                error: true,
                message: 'You must provide a uuid'
            });
        }

        if (
            !(formData.files as File).name ||
            (formData.files as File).name === 'undefined'
        ) {
            return fail(400, {
                error: true,
                message: 'You must provide a file to upload'
            });
        }

        const { files } = formData as { files: File[] };

        console.log("files", files);

        const uploadFormData = new FormData();
        uploadFormData.append('uuid', formData.uuid as string);

        if (files.length > 1) {
            files.forEach(file => {
                uploadFormData.append('files', file);
            });
        } else if (files instanceof File) {
            uploadFormData.append('files', files);
        }

        const response = await fetch(`${BASE_URL}upload_files/`, {
            method: 'POST',
            body: uploadFormData
        });

        if (!response.ok) {
            return fail(response.status, {
                error: true,
                message: 'Failed to upload files'
            });
        }

        return {
            error: false,
            message: 'Files uploaded successfully'
        };
    }
};

