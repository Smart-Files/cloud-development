/**
 * Authentication client for the smartfile API
 * 
 * Auth Process:
 * 1. Check UUID or request a new UUID from the server
 * 
 * Upload files process:
 * 2. Upload the file
 * 3. Get the file ID
 * 4. Get the file URL
 * 
 */
import { QuerySnapshot, collection, doc, getDoc, onSnapshot, query as qref, where, type DocumentChange, DocumentSnapshot } from "firebase/firestore";
import { posts, type Post, write_status, WriteStatus, files as files_store } from "../stores/posts";
import { db } from "./firestore";
import { get } from "svelte/store";
import { P } from "flowbite-svelte";

export const BASE_URL = "http://smartfile-sever-test-3-zaq4skcvqq-uc.a.run.app/"

export default class SmartfileClient {
    uuid: string;
    authenticated: boolean;

    constructor() {
        this.uuid = "";
        this.authenticated = false;
    }

    private async requestNewUUID() {
        console.log("Requesting new UUID")
        let response: Response = await fetch(BASE_URL + "auth", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });
        let json = await response.json();
        return json ? json.uuid : "";
    }


    public async auth() {
        this.uuid = await this.requestNewUUID();
        this.authenticated = true;

        console.log("Authentication Complete: ", this.authenticated, this.uuid);

        return this.authenticated ? { status: "success", uuid: this.uuid } : { status: "error", error: "Failed to authenticate" };
    }

    public async stop() {
        let response = await fetch(`${BASE_URL}stop`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ uuid: this.uuid })
        })

        return response
    }


    private createFileSafeName(filename: string): string {
        // Replace any character that is not alphanumeric, a dash, or an underscore with an underscore
        return filename.replace(/[^a-zA-Z0-9\-_\.]+/g, '_');
    }

    public async uploadFiles(files: File[]) {
        if (!this.authenticated) {
            await this.auth();
            if (!this.authenticated) {
                return { status: "error", error: "Failed to authenticate" };
            }
        }

        let formData = new FormData();
        formData.append('uuid', this.uuid);

        files.forEach(file => {
            // Create a file-safe name by removing or replacing special characters
            const fileSafeName = this.createFileSafeName(file.name);
            const fileWithSafeName = new File([file], fileSafeName, {
                type: file.type,
                lastModified: file.lastModified,
            });
            formData.append('files', fileWithSafeName);
        });

        let response = await fetch(BASE_URL + "upload_files", {
            method: 'POST',
            body: formData
        });

        files_store.set(files);



        let json = await response.json();
        return json;
    }



    // Use EventSource to begin process and listen for updates
    private async beginProcess(query: string, uuid: string) {
        const url = `${BASE_URL}process_request?query=${query}&uuid=${uuid}`;
        // Subscribe to Firestore updates for this UUID
        let processDoc = doc(db, "process", uuid)
        let eventsRef = collection(processDoc, "events")


        // const q = qref(processDoc); // Ensure correct use of query function from Firestore
        const unsubscribe = onSnapshot(doc(db, "process", uuid), (doc: DocumentSnapshot) => {
            let data = doc.data()

            if (data != undefined && data.chunks) {
                for (let chunk of data.chunks) { // Update posts only with newly added documents

                    console.log("-- data --", chunk)
                    if (chunk.status == "completed") {
                        write_status.set(WriteStatus.done);
                    }
                    if (chunk.messages && chunk.messages.length > 0) {
                        if (chunk.messages[0].content == "") {
                            console.log("Empty message")
                            continue
                        }
                    } else {
                        continue
                    }

                    console.log("FOUNDCHUNK", chunk.messages)

                    if (chunk.messages[0].content.startsWith("Invalid Format:")) {
                        continue
                    }

                    if (chunk.messages[0].content.startsWith("Command:")) {
                        let post_data = get(posts);
                        let all_posts = post_data.chats[this.uuid]
                        let new_post = all_posts[all_posts.length - 1]
                        all_posts[all_posts.length - 1] = { ...new_post, bash_output: chunk.messages[0].content }
                        posts.update(old_posts => ({ chats: { ...old_posts.chats, [this.uuid]: all_posts } }));


                    } else {
                        posts.update(posts => ({
                            chats: {
                                ...posts.chats,
                                [uuid]: [...(posts.chats[uuid] || []), chunk]
                            }
                        }));
                    }
                }
            }
        });

        write_status.set(WriteStatus.loading);


        let result = await fetch(url);

        return result

    }

    // Example usage
    public async processRequest(query: string, uuid: string) {
        const initResponse = await this.beginProcess(query, uuid);
        return initResponse
    }

    public getUUID() {
        return this.uuid;
    }

    public getAuthenticated() {
        return this.authenticated;
    }
};

