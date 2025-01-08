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
import { db } from "./firebase";
import { BASE_URL } from "$lib/constants.js"
import { get, writable } from "svelte/store";
import axios from "axios";
import { chat, write_status } from "../stores/store";
import { WriteStatus, type UploadFile } from "../stores/types";

export default class SmartfileClient {
    uuid: string;
    authenticated: boolean;

    constructor() {
        this.uuid = "";
        this.authenticated = false;
    }

    private async requestNewUUID() {
        console.log("Requesting new UUID")
        let response: Response = await fetch(BASE_URL + "authenticate");
        let json = await response.json();
        return json ? json.uuid : "";
    }


    public async auth() {
        this.uuid = await this.requestNewUUID();
        this.authenticated = true;

        console.log("Authentication Complete: ", this.authenticated, this.uuid);

        if (this.authenticated) {
            console.log("Authentication Complete: ", this.authenticated, this.uuid);
            write_status.set(WriteStatus.IDLE);
            return { status: "success", uuid: this.uuid };
        } else {
            return { status: "error", error: "Failed to authenticate" };
        }
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

    public async uploadFiles(files: UploadFile[], downloadUpdate: (percent: number, uuid: string) => void) {
        if (!this.authenticated) {
            await this.auth();
            if (!this.authenticated) {
                return { status: "error", error: "Failed to authenticate" };
            }
        }

        const fileProgress = writable(0)

        let formData = new FormData();
        formData.append('uuid', this.uuid);

        files.forEach((fileObj: UploadFile) => {
            let file = fileObj.file
            // Create a file-safe name by removing or replacing special characters
            const fileSafeName = this.createFileSafeName(file.name);
            const fileWithSafeName = new File([file], fileSafeName, {
                type: file.type,
                lastModified: file.lastModified,
            });
            formData.append('files', fileWithSafeName);
        });

        // let response = await fetch("/api/upload-files", {
        //     method: 'POST',
        //     body: formData
        // });

        const uuid = this.uuid

        let response = await axios.post("/api/upload-files", formData, {
            onUploadProgress: (progressEvent) => {
                let progress = progressEvent.loaded / (progressEvent.total || 1);
                downloadUpdate(progress, uuid);
            }
        })

        let json = await response.data;
        return { ...json, fileProgress };
    }


    public async processRequest(query: string, uuid: string) {
        // Subscribe to Firestore updates for this UUID
        write_status.set(WriteStatus.DONE);

        const formData = new FormData();
        formData.append('query', query);
        formData.append('uuid', uuid);

        const url = "/api/process-request"

        let result = await fetch(url, {
            method: 'POST',
            body: formData
        });

        return result

    }

    public getUUID() {
        return this.uuid;
    }

    public getAuthenticated() {
        return this.authenticated;
    }
};

