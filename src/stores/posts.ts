import { writable, get } from "svelte/store";
import type { Writable } from "svelte/store";
import SmartfileClient from "$lib/smartfileclient";
import { uuidv4 } from "$lib/helpers/util";
import { chat, files, uuid, write_status } from "./store";
import { Sender, WriteStatus, type Post, type UploadFile } from "./types";
import { DocumentSnapshot, QuerySnapshot, collection, doc, onSnapshot, query, where, type DocumentData } from "firebase/firestore";
import { db } from "$lib/firebase";
import { WS_URL } from "$lib/constants";


const client = new SmartfileClient();

export function usePosts() {
    async function authenticate() {
        const response = await client.auth();
        if (response.uuid) {
            uuid.set(response.uuid);
            console.log("Authentication Complete: ", client.getAuthenticated(), client.getUUID());
        } else {
            console.log("Authentication Failed: ", response);
        }
    }

    async function createChat() {
        chat.update(chatData => ({ posts: [], uuid: getUUID(), created_at: Date.now() }));
    }

    async function uploadFile(file: File, downloadUpdate: (percent: number) => void) {
        const uploadFile: UploadFile = {
            file: file,
            uuid: uuidv4(),
            name: file.name,
            uploaded: false,
            progress: 0
        }

        files.update((files: { [uuid: string]: UploadFile }) => ({
            ...files,
            [uploadFile.uuid]: {
                file: file,
                uuid: uploadFile.uuid,
                name: file.name,
                uploaded: false,
                progress: 0
            }
        }));


        const data = await client.uploadFiles([uploadFile], downloadUpdate);
        if (data.status === "success") {
            files.update((files: { [uuid: string]: UploadFile }) => ({
                ...files,
                [uploadFile.uuid]: {
                    file: uploadFile.file,
                    uuid: uploadFile.uuid,
                    name: uploadFile.name,
                    uploaded: true,
                    progress: 100
                }
            }));

            chat.update(chatData => ({
                ...chatData,
                upload_files: [...(chatData.upload_files || []), uploadFile]
            }));
        }
        return data;
    }

    async function generate(content: string) {
        await registerChatListener()

        // Create a new post object
        let new_post: Post = {
            messages: [
                { content: content }
            ],
            created_at: Date.now(),
            role: Sender.user
        }

        // Update the posts store with the new post
        chat.update(chatData => ({ ...chatData, posts: [...(chatData.posts || []), new_post] }));

        write_status.set(WriteStatus.DONE);

        let response = await client.processRequest(content, getUUID());
        return response
    }

    async function registerChatListener() {
        let _uuid = getUUID();
        let processDoc = doc(db, "process", _uuid)
        let dataCollection = collection(processDoc, "data")
        // let eventsRef = collection(processDoc, "events")

        const q = query(dataCollection);

        console.log("Connecting to WebSocket")
        const ws = new WebSocket(WS_URL + _uuid);

        ws.onerror = (error) => {
            console.error("WebSocket error observed:", error);
        }

        ws.onmessage = (event) => {
            chatUpdateEvent(event.data)
        }

        ws.onclose = () => {
            console.log("WebSocket connection closed")
        }
    }

    async function onModelStart(data: { event: string, run_id: string, content: any }) {
        let newPost: Post = {
            messages: [],
            created_at: Date.now(),
            role: Sender.bot,
            id: data.run_id
        }

        chat.update(posts => {
            return {
                ...posts,
                posts: [...posts.posts, newPost]
            }
        });
    }

    async function onModelStream(data: { event: string, run_id: string, content: any }) {
        chat.update(posts => {
            const editPosts = posts.posts.map(post => {
                if (post.id == data.run_id) {
                    return {
                        ...post,
                        messages: [...post.messages, { content: data.content.replace("\n", "<br/>") }]
                    }
                }
                return post
            })
            return {
                ...posts,
                posts: editPosts,
            }
        });
    }

    async function onAgentFinished(data: { event: string, run_id: string, files: string[] }) {
        console.log("Agent finished", data)
        chat.update(posts => {
            let newPosts = [...posts.posts]
            newPosts[newPosts.length - 1].files = data.files
            return ({
                ...posts,
                posts: newPosts
            });
        });
    }

    async function chatUpdateEvent(data: string) {
        let chunkData: { event: string, run_id: string, content: any } = JSON.parse(data);

        if (chunkData.event) write_status.set(WriteStatus.DONE);

        if (chunkData.event == "on_chat_model_start") {
            onModelStart(chunkData)
        }

        if (chunkData.event == "on_chat_model_stream") {
            onModelStream(chunkData)
        }

        if (chunkData.event == "on_chat_model_end") {
            console.log("on_chat_model_end", chunkData)
            // chat.update(posts => {
            //     let newPosts = [...posts.posts]
            //     newPosts[newPosts.length - 1].messages = [{ content: chunkData.content }]
            //     return ({
            //         ...posts,
            //         posts: newPosts
            //     });
            // });
        }

        if (chunkData.event != "on_chat_model_stream") {
            console.log(`Data received for ${chunkData.event}:`, chunkData)
        }

        let messageContent = chunkData.content;

        if (chunkData.event == "on_chat_model_end" && messageContent.startsWith("Command:")) {
            let post_data = get(chat);
            let all_posts = post_data.posts
            all_posts[all_posts.length - 1] = { ...all_posts[all_posts.length - 1], output: messageContent }
            chat.update(old_posts => ({ ...old_posts, posts: all_posts }));
        }
    }

    async function deleteFile(file_uuid: string) {
        files.update((currentFiles) => {
            const updatedFiles = { ...currentFiles };
            delete updatedFiles[file_uuid];
            return updatedFiles;
        });
    }

    async function stop() {
        let response = await client.stop();
    }

    function fetchPosts() {
        return get(chat).posts;
    }

    function getUUID() {
        return get(uuid);
    }

    function getAuthenticated() {
        return client.getAuthenticated();
    }

    return {
        deleteFile, stop,
        subscribe: chat.subscribe,
        update: chat.update,
        generate,
        fetchPosts,
        getUUID,
        getAuthenticated,
        uploadFile,
        authenticate,
        createChat
    }
}
