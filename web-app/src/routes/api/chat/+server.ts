import { kv } from '$lib/kv';
import { nanoid } from '$lib/utils';
import type { Config } from '@sveltejs/adapter-vercel';
import { OpenAIStream, StreamingTextResponse } from 'ai';
import { Configuration, OpenAIApi } from 'openai-edge';

import { env } from '$env/dynamic/private';
// You may want to replace the above with a static private env variable
// for dead-code elimination and build-time type-checking:
// import { OPENAI_API_KEY } from '$env/static/private'

import type { RequestHandler } from './$types';

const BASE_URL = "http://localhost:8000/";

export const config: Config = {
	runtime: 'edge'
};





export const POST = (async ({ request, locals: { getSession } }) => {
	fetch(BASE_URL + "auth", {
		method: "POST"
	})
		.then(response => response.json())
		.then(data => {
			console.log(data);
		});

	// Respond with the stream
	return new Response(JSON.stringify({ message: "Hello, World!" }));
}) satisfies RequestHandler;

