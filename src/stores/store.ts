import { writable } from "svelte/store";
import { WriteStatus, type Chat, type UploadFile } from "./types";

export const chat = writable<Chat>();
export const files = writable<{ [uuid: string]: UploadFile }>({});

export const input = writable<string>('');

export const uuid = writable<string>('');

export const write_status = writable<WriteStatus>(WriteStatus.LOADING);