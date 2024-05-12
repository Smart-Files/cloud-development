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

import { Regex } from "lucide-svelte";
import { posts, type Post } from "../stores/posts";

export default class SmartfileClient {
    uuid: string;
    authenticated: boolean;
    BASE_URL: string;

    constructor() {
        this.BASE_URL = "http://localhost:8080/"
        this.uuid = "";
        this.authenticated = false;
    }

    private async requestNewUUID() {
        let response: Response = await fetch(this.BASE_URL + "auth", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });
        let json = await response.json();
        return json ? json.uuid : "";
    }

    private async checkUUID(uuid: string) {
        let response: Response = await fetch(this.BASE_URL + "validate?uuid=" + uuid);

        let responseData = await response.json();

        console.log("Response", responseData)

        if (responseData.status == "authenticated") {
            return true;
        } else {
            return false;
        }
    }

    public async auth() {
        this.uuid = await this.requestNewUUID();
        this.authenticated = true;

        console.log("Authentication Complete: ", this.authenticated, this.uuid);

        return this.authenticated ? { status: "success", uuid: this.uuid } : { status: "error", error: "Failed to authenticate" };
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
            formData.append('files', file);
        });

        let response = await fetch(this.BASE_URL + "upload_files", {
            method: 'POST',
            body: formData
        });

        let json = await response.json();
        return json;
    }


    // Use EventSource to begin process and listen for updates
    private beginProcess(query: string, uuid: string) {
        const url = `${this.BASE_URL}process_request?query=${query}&uuid=${uuid}`;
        const eventSource = new EventSource(url);

        eventSource.onmessage = function (event) {
            console.log('-- DATA --\n', event.data);
            let data = JSON.parse(event.data);
            console.log('-- PARSED --\n', data);

            if (data.status == "completed") {
                console.log("Processing complete");
                eventSource.close();
                return;
            }

            if (!(data.messages)) {
                console.log("No data, skipping");
                return;
            }

            if (data.steps) {
                console.log("Steps: ", data.steps);
                return;
            }



            let content = data.messages[0].content

            let new_post: Post = {
                uuid: uuid,
                content: content,
                output: data.output,
                actions: data.actions,
                files: data.files,
                created_at: new Date().toISOString(),
                role: "bot"
            }

            posts.update(posts => ({ chats: { ...posts.chats, [uuid]: [...(posts.chats[uuid] || []), new_post] } }));
        };

        eventSource.onerror = function (error) {
            console.error('EventSource failed:', error);
            eventSource.close();
        };


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

