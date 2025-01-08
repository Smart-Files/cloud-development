export enum Sender {
    user = "user",
    bot = "bot"
}

export type Post = {
    messages: { content: string }[];
    created_at: number;
    role: Sender;
    actions?: any;
    output?: string;
    steps?: any;
    files?: string[];
    uuid?: string;
    id: string;
}

export type Chat = {
    posts: Post[];
    uuid: string;
    created_at: number;
    upload_files?: UploadFile[];
}

export type UploadFile = {
    file: File;
    uuid: string;
    name: string;
    uploaded: boolean;
    progress: number;
}

export enum WriteStatus {
    IDLE = 0,
    LOADING = 1,
    WAITING_RESPONSE = 2,
    DONE = 3,
    ERROR = 4
}