import { fail } from '@sveltejs/kit';
import { BASE_URL } from '$lib/constants';

// Process Request for chat session
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
            !(formData.query as string) ||
            (formData.query as string) === 'undefined'
        ) {
            return fail(400, {
                error: true,
                message: 'You must provide a uuid'
            });
        }

        const { query, uuid } = formData as { query: string, uuid: string };

        const uploadFormData = new FormData();
        uploadFormData.append('uuid', uuid);
        uploadFormData.append('query', query);


        const response = await fetch(BASE_URL + 'process_request/', {
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

