import { writable, get } from "svelte/store";
import type { Writable } from "svelte/store";
import SmartfileClient from "$lib/smartfileclient";

enum Sender {
    user = "user",
    bot = "bot"
}

export type Post = {
    uuid: string;
    content: string;
    files: string[] | File[];
    created_at: string;
    role: Sender;
    actions?: any;
    output?: string;

}

export type PostStore = {
    chats: {
        [uuid: string]: Post[];
    }
};

export const posts = writable<PostStore>({ chats: {} });
export const files = writable<File[]>([]);

export const input = writable<string>('');

export const uuid = writable<string>('');

export function usePosts() {
    const client = new SmartfileClient();

    client.auth().then((response) => {
        if (response.uuid) {
            uuid.set(response.uuid);
            console.log("Authentication Complete: ", client.getAuthenticated(), client.getUUID());
        } else {
            console.log("Authentication Failed: ", response);
        }
    });

    // Create a new chat for the user
    posts.update(posts => ({ chats: { ...posts.chats, [getUUID()]: [] } }));

    async function generate(content: string, files: File[]) {
        if (files.length > 0) {
            const data = await client.uploadFiles(files);
            if (data.status === "success") {
                console.log('data', data);
            }
        }

        // Create a new post object
        let new_post: Post = {
            uuid: getUUID(),
            content,
            files: files,
            created_at: new Date().toISOString(),
            role: Sender.user
        }
        // Update the posts store with the new post
        posts.update(posts => ({ chats: { ...posts.chats, [getUUID()]: [...(posts.chats[getUUID()] || []), new_post] } }));

        let response = await client.processRequest(content, getUUID());
        return response

    }



    function fetchPosts() {
        return get(posts).chats[getUUID()];
    }

    function getUUID() {
        return get(uuid);
    }

    function getAuthenticated() {
        return client.getAuthenticated();
    }

    return { subscribe: posts.subscribe, update: posts.update, generate, fetchPosts, getUUID, getAuthenticated }
}


